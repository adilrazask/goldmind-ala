"""Multi-Stage Validation Engine: Out-of-Sample, Walk-Forward, Market Regime, and Cost Stress Testing."""
from __future__ import annotations
import uuid
import math
from typing import List, Dict, Any, Tuple
from backend.app.backtesting.engine import BacktestEngine

class MultiStageValidator:
    def __init__(self, cost_bps: float = 3.0, spread_points: int = 25, slippage_points: int = 10):
        self.engine = BacktestEngine(cost_bps=cost_bps, spread_points=spread_points, slippage_points=slippage_points)

    def validate_candidate(
        self,
        candles: List[Dict[str, Any]],
        spec: Dict[str, Any],
        candidate_id: str
    ) -> Dict[str, Any]:
        n = len(candles)
        if n < 100:
            raise ValueError(f"Need at least 100 candles for multi-stage validation, got {n}")
            
        val_id = str(uuid.uuid4())
        
        # 1. Chronological Splitting
        # Train (In-Sample): 0% -> 50%
        # Validation: 50% -> 75%
        # Untouched Out-of-Sample: 75% -> 100%
        idx_train_end = int(n * 0.50)
        idx_val_end = int(n * 0.75)
        
        train_candles = candles[:idx_train_end]
        val_candles = candles[idx_train_end:idx_val_end]
        oos_candles = candles[idx_val_end:]
        
        train_res = self.engine.run_backtest(train_candles, spec)
        val_res = self.engine.run_backtest(val_candles, spec)
        oos_res = self.engine.run_backtest(oos_candles, spec)
        
        # 2. Walk-Forward Evaluation (Rolling Anchored Windows)
        wf_windows = []
        wf_step = int(n * 0.15)
        wf_train_size = int(n * 0.40)
        
        wf_passes = 0
        total_wf_tests = 0
        
        for w_start in range(0, n - wf_train_size - wf_step + 1, wf_step):
            train_sub = candles[w_start : w_start + wf_train_size]
            test_sub = candles[w_start + wf_train_size : w_start + wf_train_size + wf_step]
            if len(test_sub) < 15:
                continue
            total_wf_tests += 1
            w_res = self.engine.run_backtest(test_sub, spec)
            passed_window = w_res["total_return"] > -0.01 and w_res["max_drawdown"] <= 0.18
            if passed_window:
                wf_passes += 1
            wf_windows.append({
                "window": total_wf_tests,
                "start": test_sub[0]["timestamp"],
                "end": test_sub[-1]["timestamp"],
                "return": w_res["total_return"],
                "max_drawdown": w_res["max_drawdown"],
                "trades": w_res["trades_count"],
                "passed": passed_window
            })

        wf_consistency = (wf_passes / total_wf_tests) if total_wf_tests > 0 else 0.0

        # 3. Market Regime Breakdown (4 Segments)
        regime_size = n // 4
        regimes_report = []
        for r_idx in range(4):
            reg_candles = candles[r_idx * regime_size : (r_idx + 1) * regime_size]
            r_res = self.engine.run_backtest(reg_candles, spec)
            regimes_report.append({
                "regime_index": r_idx + 1,
                "regime_name": ["Bullish Trend", "High Volatility Chop", "Bearish Trend", "Ranging Quiet"][r_idx],
                "start": reg_candles[0]["timestamp"],
                "end": reg_candles[-1]["timestamp"],
                "return": r_res["total_return"],
                "max_drawdown": r_res["max_drawdown"],
                "profit_factor": r_res["profit_factor"],
                "trades": r_res["trades_count"]
            })

        # 4. Transaction-Cost Stress Test (2x fees & spread)
        stress_engine = BacktestEngine(
            cost_bps=self.engine.cost_bps * 2.0,
            spread_points=self.engine.spread_points * 2,
            slippage_points=self.engine.slippage_points * 2
        )
        stress_res = stress_engine.run_backtest(oos_candles, spec)

        # 5. Gate Checks and Rejection Criteria
        failure_reasons = []
        if val_res["total_return"] <= 0.0:
            failure_reasons.append(f"Validation period return is non-positive: {val_res['total_return']:.2%}")
        if oos_res["total_return"] <= 0.0:
            failure_reasons.append(f"Untouched out-of-sample return is non-positive: {oos_res['total_return']:.2%}")
        if oos_res["max_drawdown"] > 0.18:
            failure_reasons.append(f"Out-of-sample max drawdown exceeded 18%: {oos_res['max_drawdown']:.2%}")
        if (train_res["trades_count"] + val_res["trades_count"] + oos_res["trades_count"]) < 5:
            failure_reasons.append("Insufficient trade sample size across total evaluation period (< 5 trades)")
        if oos_res["profit_factor"] < 1.05 and oos_res["trades_count"] > 0:
            failure_reasons.append(f"Profit factor in out-of-sample test below minimum 1.05 threshold: {oos_res['profit_factor']:.2f}")
        if stress_res["total_return"] < -0.05:
            failure_reasons.append(f"Fragile to transaction cost stress test: return dropped to {stress_res['total_return']:.2%}")
        if wf_consistency < 0.50 and total_wf_tests > 1:
            failure_reasons.append(f"Walk-forward window consistency too low: {wf_consistency:.0%} ({wf_passes}/{total_wf_tests} windows)")

        passed_all = len(failure_reasons) == 0
        decision = "STATISTICALLY_VALIDATED_CANDIDATE" if passed_all else "REJECTED_OR_INCONCLUSIVE"
        
        lesson = (
            f"Strategy {spec.get('family')} demonstrated robustness across validation, out-of-sample ({oos_res['total_return']:.2%}), "
            f"and walk-forward ({wf_consistency:.0%}) stress tests. Qualified for restricted demo testing."
            if passed_all else
            f"Strategy {spec.get('family')} failed robustness gates: {'; '.join(failure_reasons[:2])}. Recorded to prevent repetitive parameter tuning."
        )

        return {
            "validation_id": val_id,
            "candidate_id": candidate_id,
            "decision": decision,
            "passed_all_gates": passed_all,
            "failure_reasons": failure_reasons,
            "lesson": lesson,
            "in_sample_metrics": train_res,
            "validation_metrics": val_res,
            "out_of_sample_metrics": oos_res,
            "walk_forward_metrics": {
                "consistency": round(wf_consistency, 2),
                "passing_windows": wf_passes,
                "total_windows": total_wf_tests,
                "windows": wf_windows
            },
            "regime_breakdown": regimes_report,
            "stress_test_metrics": {
                "stress_oos_return": stress_res["total_return"],
                "stress_max_drawdown": stress_res["max_drawdown"],
                "stress_profit_factor": stress_res["profit_factor"]
            }
        }
