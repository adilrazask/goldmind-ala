"""Safe strategy generation: candidates are declarative specs, never arbitrary executed code."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math, uuid
from .market_data import Candle

@dataclass
class CandidateReport:
    candidate_id: str
    family: str
    parameters: dict
    observations: int
    train_return: float
    test_return: float
    test_max_drawdown: float
    test_win_rate: float
    trades: int
    score: float
    decision: str
    lesson: str
    def to_dict(self): return asdict(self)

ALLOWED_FAMILIES = {"sma_crossover", "momentum", "breakout", "rsi_mean_reversion"}

def generate_candidates() -> list[dict]:
    """Generate bounded, inspectable strategy specifications from an allowlisted DSL."""
    out=[]
    for fast in (5, 8, 10, 15):
        for slow in (20, 30, 40, 50):
            if fast < slow: out.append({"family":"sma_crossover", "fast":fast, "slow":slow, "side":"long_only"})
    for lookback in (3, 5, 8, 12):
        for threshold in (0.001, 0.002, 0.004):
            out.append({"family":"momentum", "lookback":lookback, "threshold":threshold, "side":"long_only"})
    for lookback in (10, 20, 30):
        for breakout_pct in (0.0005, 0.001, 0.002):
            out.append({"family":"breakout", "lookback":lookback, "breakout_pct":breakout_pct, "side":"long_only"})
    for period in (7, 10, 14):
        for lower in (20, 25, 30):
            out.append({"family":"rsi_mean_reversion", "period":period, "lower":lower, "exit_level":50, "side":"long_only"})
    return out

def _rsi(values: list[float], end: int, period: int) -> float:
    if end < period: return 50.0
    gains=[]; losses=[]
    for i in range(end-period+1, end+1):
        delta=values[i]-values[i-1]
        gains.append(max(delta,0.0)); losses.append(max(-delta,0.0))
    avg_gain=sum(gains)/period; avg_loss=sum(losses)/period
    if avg_loss == 0: return 100.0 if avg_gain else 50.0
    rs=avg_gain/avg_loss
    return 100.0-(100.0/(1.0+rs))

def _position_series(closes: list[float], spec: dict) -> list[float]:
    family=spec.get("family")
    if family not in ALLOWED_FAMILIES: raise ValueError(f"Unsupported strategy family: {family}")
    n=len(closes); pos=[0.0]*n
    if family == "sma_crossover":
        fast=int(spec["fast"]); slow=int(spec["slow"])
        if not (2 <= fast < slow <= 200): raise ValueError("Invalid SMA parameters")
        for i in range(slow-1,n-1):
            pos[i+1]=1.0 if sum(closes[i-fast+1:i+1])/fast > sum(closes[i-slow+1:i+1])/slow else 0.0
    elif family == "momentum":
        lookback=int(spec["lookback"]); threshold=float(spec["threshold"])
        if not (1 <= lookback <= 100 and 0 <= threshold <= .1): raise ValueError("Invalid momentum parameters")
        for i in range(lookback,n-1): pos[i+1]=1.0 if closes[i]/closes[i-lookback]-1.0 > threshold else 0.0
    elif family == "breakout":
        lookback=int(spec["lookback"]); pct=float(spec["breakout_pct"])
        if not (2 <= lookback <= 100 and 0 <= pct <= .1): raise ValueError("Invalid breakout parameters")
        for i in range(lookback,n-1): pos[i+1]=1.0 if closes[i] > max(closes[i-lookback:i])*(1+pct) else 0.0
    elif family == "rsi_mean_reversion":
        period=int(spec["period"]); lower=float(spec["lower"]); exit_level=float(spec.get("exit_level",50))
        if not (2 <= period <= 100 and 5 <= lower <= 45 and lower < exit_level <= 80): raise ValueError("Invalid RSI parameters")
        holding=False
        for i in range(period,n-1):
            rsi=_rsi(closes,i,period)
            if not holding and rsi < lower: holding=True
            elif holding and rsi >= exit_level: holding=False
            pos[i+1]=1.0 if holding else 0.0
    return pos

def _metrics(returns: list[float]) -> tuple[float,float,float,int]:
    equity=peak=1.0; dd=0.0; active=wins=0
    for r in returns:
        equity *= max(1e-12,1.0+r); peak=max(peak,equity); dd=max(dd,(peak-equity)/peak)
        if abs(r)>1e-12: active+=1; wins+=int(r>0)
    return equity-1,dd,(wins/active if active else 0.0),active

def evaluate_candidate(candles: list[Candle], spec: dict, cost_bps: float=3.0) -> CandidateReport:
    if len(candles)<100: raise ValueError("Need at least 100 candles for strategy-lab evaluation")
    if not math.isfinite(cost_bps) or cost_bps<0 or cost_bps>100: raise ValueError("cost-bps must be between 0 and 100")
    closes=[c["close"] for c in candles]; positions=_position_series(closes,spec)
    returns=[0.0]*len(closes)
    for i in range(1,len(closes)):
        market=closes[i]/closes[i-1]-1
        turnover=abs(positions[i]-positions[i-1])
        returns[i]=positions[i-1]*market-turnover*(cost_bps/10000.0)
    split=int(len(returns)*.7)
    train,_,_,_= _metrics(returns[1:split]); test,dd,wr,trades=_metrics(returns[split:])
    # This is a triage score, not a probability and not an investment recommendation.
    score=(test*100.0) - (dd*35.0) + (min(trades,100)/100.0)
    passed=math.isfinite(test) and test>0 and dd<=.15 and trades>=3
    decision="CANDIDATE_FOR_FURTHER_VALIDATION" if passed else "REJECT_OR_REVISE"
    lesson=("Preliminary holdout passed a simple gate; run fresh out-of-sample and walk-forward tests with realistic broker costs." if passed else "Did not pass preliminary holdout gate; preserve result and do not tune repeatedly against this same holdout.")
    return CandidateReport(str(uuid.uuid4()),spec["family"],dict(spec),len(candles),round(train,6),round(test,6),round(dd,6),round(wr,6),trades,round(score,6),decision,lesson)


def generate_model_candidate(objective: str, prior_lessons: list[str] | None = None) -> dict | None:
    """Ask Ollama for a declarative spec; validate against the local allowlist. Never execute model code."""
    import os, json, urllib.request
    if os.getenv("ALA_USE_OLLAMA", "0").lower() not in {"1", "true", "yes"}: return None
    host=os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model=os.getenv("OLLAMA_MODEL", "qwen3:8b")
    prompt=("Return ONLY one JSON object for a candidate trading strategy spec. Do not return code. "
      "Allowed schemas: {family:sma_crossover,fast:int,slow:int,side:long_only}; "
      "{family:momentum,lookback:int,threshold:number,side:long_only}; "
      "{family:breakout,lookback:int,breakout_pct:number,side:long_only}; "
      "{family:rsi_mean_reversion,period:int,lower:number,exit_level:number,side:long_only}. "
      "No leverage, no shorting, no broker actions, no claims of profitability. "
      f"Objective: {objective}. Prior lessons: {(prior_lessons or [])[-5:]}")
    payload=json.dumps({"model":model,"prompt":prompt,"stream":False,"format":"json"}).encode()
    req=urllib.request.Request(f"{host}/api/generate",data=payload,headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=20) as response: body=json.loads(response.read().decode())
        spec=json.loads(body.get("response",""))
        # Run through the same parameter validation used by the backtest engine.
        if spec.get("family") not in ALLOWED_FAMILIES or spec.get("side") != "long_only": return None
        _position_series([100.0 + i*0.1 for i in range(250)], spec)
        return spec
    except Exception:
        return None
