import argparse, itertools, json, os, time
from ala.agent import AutonomousLearningAgent
from ala.memory import MemoryStore
from ala.market_data import load_ohlcv_csv
from ala.csv_backtest import run_sma_backtest
from ala.strategy_lab import generate_candidates, evaluate_candidate, generate_model_candidate
from ala.learning import choose_next_candidate, record_experience


def print_history(memory):
    history=memory.recent_results(limit=20)
    candidates=memory.candidate_history(20)
    if not history and not candidates:
        print("No experiments stored yet. Run the agent first."); return
    for item in history:
        print(f"- {item['created_at']} | {item.get('decision','UNKNOWN')} | {item.get('strategy_name',item.get('strategy','experiment'))} | {item.get('objective','research')}")
        print(f"  Lesson: {item.get('lesson','No lesson recorded')}")
    for item in candidates:
        print(f"- {item['created_at']} | {item['status']} | {item['family']} | score={item['score']}")
        print(f"  Lesson: {(item.get('result_json') or {}).get('lesson','No lesson recorded')}")

def save_backtest(memory, report):
    from types import SimpleNamespace
    payload=report.to_dict(); payload['objective']=f"CSV SMA backtest {report.fast_window}/{report.slow_window}"
    payload['hypothesis']="A long-only SMA crossover may show positive performance on the chronological test segment."
    payload['train_return']=report.train_return; payload['test_return']=report.test_return
    payload['test_max_drawdown']=report.test_max_drawdown; payload['test_win_rate']=report.test_win_rate
    payload['validation_passed']=report.validation_passed
    memory.save_result(SimpleNamespace(experiment_id=report.experiment_id,objective=payload['objective'],hypothesis=payload['hypothesis'],to_dict=lambda:payload))

def run_research_cycle(memory, candles, cost_bps, objective="Find and evaluate a new candidate strategy"):
    lessons=[x.get("lesson","") for x in memory.recent_results(10)]
    model_spec=generate_model_candidate(objective,lessons)
    spec=model_spec or choose_next_candidate(memory)
    report=evaluate_candidate(candles,spec,cost_bps)
    record_experience(memory,report)
    return spec,report

def mt5_autopilot(args, memory):
    if args.mode != "demo":
        raise SystemExit("Autonomous MT5 mode is demo-only. Live orders are manual-command only and require separate explicit confirmation.")
    from ala.mt5_gateway import MT5Gateway
    from ala.strategy_lab import _position_series
    gateway=MT5Gateway(mode="demo")
    try:
        print("Connected to MT5 DEMO account:")
        print(json.dumps(gateway.status(),indent=2))
        cycle=0
        while True:
            cycle+=1
            candles=gateway.rates(args.symbol,args.timeframe,args.bars)
            spec,report=run_research_cycle(memory,candles,args.cost_bps,f"Research {args.symbol} {args.timeframe}")
            print(f"Cycle {cycle}: {spec} -> {report.decision}; test={report.test_return:.3%}; DD={report.test_max_drawdown:.2%}")
            positions=_position_series([c["close"] for c in candles],spec)
            target=positions[-1] if positions else 0.0
            own=[p for p in gateway.positions(args.symbol) if p["magic"]==610181]
            if args.trade:
                if report.decision!="CANDIDATE_FOR_FURTHER_VALIDATION":
                    print("No demo order: candidate did not pass preliminary research gate.")
                elif target > 0 and not own:
                    result=gateway.execute_market_order(args.symbol,"buy",args.risk_percent,args.sl_points,args.tp_points)
                    print("DEMO ORDER:",json.dumps(result.to_dict(),indent=2))
                elif target <= 0 and own:
                    print("DEMO SIGNAL EXIT:",json.dumps(gateway.close_ala_positions(args.symbol),indent=2))
                else:
                    print("No demo order: target state already matches current ALA position state.")
            else:
                print("Research-only cycle. To allow demo orders, restart with --trade. No order was sent.")
            if not args.forever and cycle>=args.cycles: break
            time.sleep(max(30,args.interval))
    except KeyboardInterrupt:
        print("Stopped by keyboard interrupt. No new orders will be submitted.")
    finally:
        gateway.close()

def main():
    parser=argparse.ArgumentParser(description="GoldMind ALA Standalone v0.3 — research-first autonomous agent")
    sub=parser.add_subparsers(dest="command",required=True)
    run_cmd=sub.add_parser("run",help="run a bounded synthetic workflow check"); run_cmd.add_argument("--objective",required=True)
    back=sub.add_parser("backtest",help="backtest SMA crossover on historical OHLCV CSV"); back.add_argument("--csv",required=True); back.add_argument("--fast",type=int,default=10); back.add_argument("--slow",type=int,default=30); back.add_argument("--cost-bps",type=float,default=3.0)
    auto=sub.add_parser("autopilot",help="autonomously generate/evaluate strategy specs from CSV data"); auto.add_argument("--csv",required=True); auto.add_argument("--cycles",type=int,default=6); auto.add_argument("--cost-bps",type=float,default=3.0); auto.add_argument("--interval",type=int,default=3600); auto.add_argument("--forever",action="store_true",help="continue until Ctrl+C; CSV does not update automatically")
    lab=sub.add_parser("generate",help="generate and evaluate one new strategy specification"); lab.add_argument("--csv",required=True); lab.add_argument("--cost-bps",type=float,default=3.0); lab.add_argument("--objective",default="Find a robust strategy hypothesis")
    sub.add_parser("history",help="show stored experiment history"); sub.add_parser("instructions",help="show persistent instructions")
    addi=sub.add_parser("add-instruction",help="save an instruction"); addi.add_argument("--text",required=True)
    example=sub.add_parser("add-example",help="save a demonstration/example"); example.add_argument("--title",required=True); example.add_argument("--lesson",required=True)
    sub.add_parser("examples",help="show saved examples")
    srv=sub.add_parser("server",help="start FastAPI REST and WebSocket backend server")
    srv.add_argument("--host",default="127.0.0.1")
    srv.add_argument("--port",type=int,default=8000)
    status=sub.add_parser("mt5-status",help="show MT5 account status; Windows + MT5 terminal required"); status.add_argument("--mode",choices=["demo","live"],default="demo"); status.add_argument("--confirm-live",default=None)
    trade=sub.add_parser("mt5-trade",help="send one guarded manual market order; demo mode by default")
    trade.add_argument("--mode",choices=["demo","live"],default="demo"); trade.add_argument("--symbol",required=True); trade.add_argument("--side",choices=["buy","sell"],required=True); trade.add_argument("--risk-percent",type=float,default=0.25); trade.add_argument("--sl-points",type=int,default=300); trade.add_argument("--tp-points",type=int,default=600); trade.add_argument("--confirm-live",default=None)
    mtauto=sub.add_parser("mt5-autopilot",help="continuous strategy research; optional DEMO-only order testing")
    mtauto.add_argument("--mode",choices=["demo"],default="demo"); mtauto.add_argument("--symbol",required=True); mtauto.add_argument("--timeframe",choices=["M1","M5","M15","M30","H1","H4","D1"],default="M15"); mtauto.add_argument("--bars",type=int,default=500); mtauto.add_argument("--cycles",type=int,default=1); mtauto.add_argument("--interval",type=int,default=900); mtauto.add_argument("--forever",action="store_true"); mtauto.add_argument("--trade",action="store_true",help="explicitly allow DEMO orders; omitted means research only"); mtauto.add_argument("--risk-percent",type=float,default=0.25); mtauto.add_argument("--sl-points",type=int,default=300); mtauto.add_argument("--tp-points",type=int,default=600); mtauto.add_argument("--cost-bps",type=float,default=3.0)
    args=parser.parse_args(); memory=MemoryStore(); agent=AutonomousLearningAgent(memory)
    if args.command=="run":
        plan,result=agent.run(args.objective); print("=== PLAN ==="); print(json.dumps(plan,indent=2)); print("=== RESULT (SYNTHETIC DATA ONLY) ==="); print(result.to_json()); print("Synthetic results are not evidence of market profitability.")
    elif args.command=="backtest":
        candles=load_ohlcv_csv(args.csv); report=run_sma_backtest(candles,args.fast,args.slow,args.cost_bps); save_backtest(memory,report); print(report.to_json())
    elif args.command in {"autopilot","generate"}:
        candles=load_ohlcv_csv(args.csv)
        if args.command=="generate":
            spec,report=run_research_cycle(memory,candles,args.cost_bps,args.objective); print("SPEC:",json.dumps(spec,indent=2)); print(json.dumps(report.to_dict(),indent=2))
        else:
            if not 1<=args.cycles<=10000: raise SystemExit("--cycles must be between 1 and 10000")
            cycle=0
            try:
                while True:
                    cycle+=1; spec,report=run_research_cycle(memory,candles,args.cost_bps)
                    print(f"Cycle {cycle}: {json.dumps(spec)} -> {report.decision}; test={report.test_return:.3%}; DD={report.test_max_drawdown:.2%}; score={report.score:.4f}")
                    if not args.forever and cycle>=args.cycles: break
                    time.sleep(max(1,args.interval))
            except KeyboardInterrupt: print("Stopped by keyboard interrupt.")
            print("Warning: repeated research on a fixed CSV does not add new evidence; avoid selecting a winner by test return alone.")
    elif args.command=="history": print_history(memory)
    elif args.command=="instructions":
        for i,x in enumerate(memory.get_instructions(),1): print(f"{i}. {x}")
    elif args.command=="add-instruction": memory.add_instruction(args.text); print("Instruction saved.")
    elif args.command=="add-example": memory.add_example(args.title,args.lesson); print("Example saved.")
    elif args.command=="examples":
        examples=memory.get_examples()
        if not examples: print("No saved examples.")
        for e in examples: print(f"- {e['title']}: {e['lesson']}")
    elif args.command=="server":
        import uvicorn
        print(f"Starting GoldMind ALA FastAPI Backend on http://{args.host}:{args.port}")
        uvicorn.run("backend.app.main:app", host=args.host, port=args.port, reload=False)
    elif args.command in {"mt5-status","mt5-trade"}:
        from ala.mt5_gateway import MT5Gateway
        gateway=MT5Gateway(args.mode,args.confirm_live)
        try:
            print(json.dumps(gateway.status(),indent=2))
            if args.command=="mt5-trade":
                if args.mode=="live":
                    print("LIVE ORDER REQUEST: explicit live mode enabled. Confirm account, symbol, volume/risk, SL/TP and current market conditions.")
                result=gateway.execute_market_order(args.symbol,args.side,args.risk_percent,args.sl_points,args.tp_points)
                print(json.dumps(result.to_dict(),indent=2))
        finally: gateway.close()
    elif args.command=="mt5-autopilot": mt5_autopilot(args,memory)

if __name__=="__main__": main()
