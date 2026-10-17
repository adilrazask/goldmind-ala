"""Agent Controller: Orchestrates planning, memory retrieval, task execution, and learning loops."""
from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.database.session import SessionLocal
from backend.app.models.entities import (
    AgentObjective, AgentTask, TaskEvent, StrategyCandidate, 
    ExperimentRun, BacktestResult, ValidationResult, Lesson, SystemHealth
)
from backend.app.market_data.manager import MarketDataManager
from backend.app.strategy_factory.generator import generate_family_candidates, generate_all_candidates
from backend.app.sandbox.validator import verify_sandbox_execution
from backend.app.backtesting.engine import BacktestEngine
from backend.app.validation.validator import MultiStageValidator
from backend.app.learning.memory_system import AutonomousMemorySystem
from backend.app.planner.planner import ResearchPlanner
from backend.app.agent.tools import BoundedToolRegistry

class AgentController:
    def __init__(self):
        self.data_mgr = MarketDataManager()
        self.validator = MultiStageValidator()
        self.memory_system = AutonomousMemorySystem()
        self.planner = ResearchPlanner()
        self.tool_registry = BoundedToolRegistry(self.data_mgr, self.validator)
        self.active_objective_id: Optional[str] = None
        self.operating_mode: str = "RESEARCH_ONLY" # RESEARCH_ONLY, DEMO, LIVE_DISABLED
        self.is_research_paused: bool = False

    def create_objective(self, raw_prompt: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Creates an objective, parses intent, and populates the task queue in database."""
        obj_id = f"obj_{uuid.uuid4().hex[:8]}"
        parsed = self.planner.parse_objective(raw_prompt)
        obj_title = title or f"Research {parsed['target_family']} on {parsed['instrument']} ({parsed['timeframe']})"
        
        db = SessionLocal()
        try:
            obj_record = AgentObjective(
                id=obj_id,
                title=obj_title,
                raw_prompt=raw_prompt,
                status="ACTIVE",
                parsed_intent=parsed,
                priority=1
            )
            db.add(obj_record)
            
            # Create planned tasks
            planned_tasks = self.planner.generate_plan(obj_id, parsed)
            for t in planned_tasks:
                task_record = AgentTask(
                    id=t["task_id"],
                    objective_id=obj_id,
                    task_type=t["task_type"],
                    status="PENDING",
                    input_data=t["input_data"],
                    resource_budget=t["resource_budget"]
                )
                db.add(task_record)
                
            db.commit()
            self.active_objective_id = obj_id
            return {
                "objective_id": obj_id,
                "title": obj_title,
                "parsed_intent": parsed,
                "tasks_count": len(planned_tasks)
            }
        finally:
            db.close()

    def run_next_task(self, objective_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Executes the next pending task for an objective, logs events, and records outcomes."""
        if self.is_research_paused:
            return {"status": "PAUSED", "message": "Research task execution is currently paused by operator."}

        target_obj_id = objective_id or self.active_objective_id
        if not target_obj_id:
            return None

        db = SessionLocal()
        try:
            task = db.query(AgentTask).filter_by(
                objective_id=target_obj_id, status="PENDING"
            ).order_by(AgentTask.created_at.asc()).first()
            
            if not task:
                # Mark objective completed if all tasks are done
                obj = db.query(AgentObjective).filter_by(id=target_obj_id).first()
                if obj and obj.status == "ACTIVE":
                    obj.status = "COMPLETED"
                    db.commit()
                return None

            task.status = "RUNNING"
            task.started_at = datetime.now(timezone.utc)
            db.commit()

            obj = db.query(AgentObjective).filter_by(id=task.objective_id).first()
            parsed = obj.parsed_intent if obj else {"instrument": "XAUUSD", "timeframe": "M15", "target_family": "momentum"}
            
            event_log = []
            output_data = {}
            
            # Execute specific task type
            if task.task_type == "DATA_PREPARATION":
                inst = parsed.get("instrument", "XAUUSD")
                tf = parsed.get("timeframe", "M15")
                candles, audit = self.data_mgr.generate_regime_dataset(symbol=inst, timeframe=tf, bars=600)
                output_data = {"symbol": inst, "timeframe": tf, "bars_count": len(candles), "audit": audit}
                event_log.append(f"Loaded {len(candles)} {inst} {tf} bars. Data quality audit: {audit['is_valid']}")

            elif task.task_type == "STRATEGY_GENERATION":
                fam = parsed.get("target_family", "momentum")
                inst = parsed.get("instrument", "XAUUSD")
                tf = parsed.get("timeframe", "M15")
                candidates = generate_family_candidates(fam, inst, tf)
                selected_candidate = candidates[0] if candidates else {
                    "family": fam, "instrument": inst, "timeframe": tf, "parameters": {"lookback": 5, "threshold": 0.002}
                }
                
                # Verify in sandbox
                cand_id = f"cand_{uuid.uuid4().hex[:8]}"
                passed, sandbox_msg = verify_sandbox_execution(selected_candidate)
                
                # Save candidate to DB
                cand_db = StrategyCandidate(
                    candidate_id=cand_id,
                    family=fam,
                    instrument=inst,
                    timeframe=tf,
                    hypothesis=selected_candidate.get("hypothesis", ""),
                    spec_json=selected_candidate,
                    status="SYNTAX_PASSED" if passed else "REJECTED",
                    approval_state="RESEARCH_ONLY"
                )
                db.add(cand_db)
                output_data = {"candidate_id": cand_id, "family": fam, "spec": selected_candidate, "sandbox_passed": passed}
                event_log.append(f"Candidate {cand_id} ({fam}) generated and tested in sandbox: {sandbox_msg}")

            elif task.task_type == "BACKTEST_EVALUATION":
                # Find candidate
                cand_db = db.query(StrategyCandidate).filter_by(
                    family=parsed.get("target_family", "momentum"),
                    instrument=parsed.get("instrument", "XAUUSD")
                ).order_by(StrategyCandidate.created_at.desc()).first()
                
                inst = parsed.get("instrument", "XAUUSD")
                tf = parsed.get("timeframe", "M15")
                candles, _ = self.data_mgr.generate_regime_dataset(symbol=inst, timeframe=tf, bars=600)
                spec = cand_db.spec_json if cand_db else {"family": "momentum", "parameters": {"lookback": 5, "threshold": 0.002}}
                
                engine = BacktestEngine(cost_bps=3.0, spread_points=25, slippage_points=10)
                res = engine.run_backtest(candles, spec)
                
                # Save experiment run
                exp_id = f"exp_{uuid.uuid4().hex[:8]}"
                exp_db = ExperimentRun(
                    id=exp_id,
                    task_id=task.id,
                    candidate_id=cand_db.candidate_id if cand_db else "sample_cand",
                    status="COMPLETED",
                    train_return=res["total_return"],
                    test_return=res["total_return"],
                    test_max_drawdown=res["max_drawdown"],
                    test_win_rate=res["win_rate"],
                    trades_count=res["trades_count"],
                    full_metrics=res
                )
                db.add(exp_db)
                
                btest_db = BacktestResult(
                    id=f"bt_{uuid.uuid4().hex[:8]}",
                    experiment_id=exp_id,
                    equity_curve=res["equity_curve"],
                    drawdown_curve=res["drawdown_curve"],
                    trades_log=res["trades_log"],
                    sharpe_ratio=res["sharpe_ratio"],
                    sortino_ratio=res["sortino_ratio"],
                    profit_factor=res["profit_factor"],
                    expectancy=res["expectancy"],
                    total_fees=res["total_fees"],
                    slippage_cost=res["total_slippage"]
                )
                db.add(btest_db)
                output_data = {"experiment_id": exp_id, "return": res["total_return"], "drawdown": res["max_drawdown"], "profit_factor": res["profit_factor"]}
                event_log.append(f"Completed backtest: Return {res['total_return']:.2%}, Max DD {res['max_drawdown']:.2%}, Profit Factor {res['profit_factor']:.2f}")

            elif task.task_type == "STATISTICAL_VALIDATION":
                cand_db = db.query(StrategyCandidate).order_by(StrategyCandidate.created_at.desc()).first()
                inst = parsed.get("instrument", "XAUUSD")
                tf = parsed.get("timeframe", "M15")
                candles, _ = self.data_mgr.generate_regime_dataset(symbol=inst, timeframe=tf, bars=600)
                spec = cand_db.spec_json if cand_db else {"family": "momentum", "parameters": {"lookback": 5, "threshold": 0.002}}
                
                val_res = self.validator.validate_candidate(candles, spec, cand_db.candidate_id if cand_db else "cand_1")
                
                # Save validation result
                val_db = ValidationResult(
                    id=val_res["validation_id"],
                    candidate_id=cand_db.candidate_id if cand_db else "cand_1",
                    in_sample_metrics=val_res["in_sample_metrics"],
                    validation_metrics=val_res["validation_metrics"],
                    out_of_sample_metrics=val_res["out_of_sample_metrics"],
                    walk_forward_metrics=val_res["walk_forward_metrics"],
                    regime_breakdown=val_res["regime_breakdown"],
                    stress_test_metrics=val_res["stress_test_metrics"],
                    passed_all_gates=val_res["passed_all_gates"],
                    decision=val_res["decision"],
                    failure_reasons=val_res["failure_reasons"]
                )
                db.add(val_db)
                
                if cand_db:
                    cand_db.validation_status = "PASSED" if val_res["passed_all_gates"] else "REJECTED"
                    cand_db.approval_state = "DEMO_APPROVED" if val_res["passed_all_gates"] else "RESEARCH_ONLY"
                    cand_db.status = "PROMOTED_TO_DEMO" if val_res["passed_all_gates"] else "REJECTED"
                    
                output_data = {"passed": val_res["passed_all_gates"], "decision": val_res["decision"], "failure_reasons": val_res["failure_reasons"]}
                event_log.append(f"Validation completed: Decision={val_res['decision']}, Passed={val_res['passed_all_gates']}")

            elif task.task_type == "KNOWLEDGE_SYNTHESIS":
                val_db = db.query(ValidationResult).order_by(ValidationResult.created_at.desc()).first()
                cand_db = db.query(StrategyCandidate).order_by(StrategyCandidate.created_at.desc()).first()
                fam = cand_db.family if cand_db else "General Strategy"
                
                if val_db and val_db.passed_all_gates:
                    obs = f"{fam} showed positive persistence across in-sample, out-of-sample, and walk-forward evaluations."
                    evid = f"OOS return: {val_db.out_of_sample_metrics.get('total_return', 0):.2%}, WF consistency: {val_db.walk_forward_metrics.get('consistency', 0):.0%}."
                else:
                    reasons = val_db.failure_reasons if val_db else ["Unfavorable risk-to-reward"]
                    obs = f"{fam} failed out-of-sample robustness thresholds on {parsed.get('instrument', 'XAUUSD')} {parsed.get('timeframe', 'M15')}."
                    evid = f"Failure reasons: {'; '.join(reasons[:2])}."
                    
                lesson_id = self.memory_system.record_lesson(
                    observation=obs,
                    evidence=evid,
                    applicable_conditions=f"{parsed.get('instrument', 'XAUUSD')} {parsed.get('timeframe', 'M15')}"
                )
                output_data = {"lesson_id": lesson_id, "observation": obs, "evidence": evid}
                event_log.append(f"Recorded lesson {lesson_id} into Experience Memory.")

            # Record task event
            for ev in event_log:
                db.add(TaskEvent(task_id=task.id, event_type="INFO", message=ev))
                
            task.status = "COMPLETED"
            task.finished_at = datetime.now(timezone.utc)
            task.output_data = output_data
            db.commit()
            
            return {
                "task_id": task.id,
                "task_type": task.task_type,
                "status": "COMPLETED",
                "output": output_data,
                "events": event_log
            }
        except Exception as e:
            if task:
                task.status = "FAILED"
                task.error_message = str(e)
                task.finished_at = datetime.now(timezone.utc)
                db.add(TaskEvent(task_id=task.id, event_type="ERROR", message=f"Task failed: {str(e)}"))
                db.commit()
            raise e
        finally:
            db.close()
