import React, { useState, useEffect } from 'react';
import {
  LineChart as ChartIcon,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Layers,
  TrendingUp,
  DollarSign,
  ShieldCheck,
  Activity
} from 'lucide-react';
import { api } from '../api';
import { SimpleChart } from '../components/SimpleChart';

export const BacktestPage: React.FC = () => {
  const [backtests, setBacktests] = useState<any[]>([]);
  const [validations, setValidations] = useState<any[]>([]);
  const [selectedBt, setSelectedBt] = useState<any | null>(null);
  const [selectedVal, setSelectedVal] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [btData, valData] = await Promise.all([
        api.getBacktestResults(),
        api.getValidationResults()
      ]);
      setBacktests(btData);
      setValidations(valData);
      if (btData.length > 0 && !selectedBt) {
        setSelectedBt(btData[0]);
      }
      if (valData.length > 0 && !selectedVal) {
        setSelectedVal(valData[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center">Loading backtesting and validation laboratory...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <ChartIcon className="w-5 h-5 text-amber-400" />
            Backtesting & Multi-Stage Validation
          </h1>
          <p className="text-xs text-slate-400">
            Chronological holdouts, walk-forward analysis, turnover/slippage drag, and regime-segmented stress testing.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Primary Quantitative Performance Cards */}
      {selectedBt && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-400">Sharpe Ratio</span>
            <div className={`text-base font-bold font-mono ${selectedBt.sharpe_ratio >= 1.0 ? 'text-emerald-400' : 'text-slate-200'}`}>
              {selectedBt.sharpe_ratio?.toFixed(2)}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-400">Profit Factor</span>
            <div className={`text-base font-bold font-mono ${selectedBt.profit_factor >= 1.2 ? 'text-emerald-400' : 'text-slate-200'}`}>
              {selectedBt.profit_factor?.toFixed(2)}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-400">Sortino Ratio</span>
            <div className="text-base font-bold font-mono text-slate-200">
              {selectedBt.sortino_ratio?.toFixed(2)}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-400">Trades Executed</span>
            <div className="text-base font-bold font-mono text-amber-400">
              {selectedBt.trades_count}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-400">Total Fees (bps)</span>
            <div className="text-base font-bold font-mono text-rose-400">
              ${selectedBt.total_fees?.toFixed(2)}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-400">Slippage Drag</span>
            <div className="text-base font-bold font-mono text-rose-400">
              ${selectedBt.slippage_cost?.toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* Interactive Charts: Equity & Drawdown Curves */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <SimpleChart
            data={selectedBt?.equity_curve || []}
            valueKey="equity"
            color="#10b981"
            fillColor="rgba(16, 185, 129, 0.12)"
            height={200}
            label="Historical Equity Curve ($)"
          />
        </div>
        <div>
          <SimpleChart
            data={selectedBt?.drawdown_curve || []}
            valueKey="drawdown"
            color="#ef4444"
            fillColor="rgba(239, 68, 68, 0.12)"
            height={200}
            label="Underwater Drawdown Trajectory"
            isPercentage={true}
          />
        </div>
      </div>

      {/* Multi-Stage Validation Protocol Inspector */}
      {selectedVal && (
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Multi-Stage Statistical Gate Assessment
              </h3>
              <p className="text-xs text-slate-400">Candidate: {selectedVal.candidate_id}</p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-mono font-bold ${
                selectedVal.passed_all_gates
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              }`}
            >
              {selectedVal.passed_all_gates ? 'STATISTICALLY CERTIFIED FOR DEMO' : 'REJECTED AT VALIDATION GATE'}
            </span>
          </div>

          {/* Chronological Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            {/* Split 1 */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-slate-500 text-[10px] uppercase font-bold">1. In-Sample (Train 50%)</span>
              <div className="text-slate-200">
                Return: <strong className="text-emerald-400">{(selectedVal.in_sample?.total_return * 100 || 0).toFixed(2)}%</strong>
              </div>
              <div className="text-slate-400">Max DD: {(selectedVal.in_sample?.max_drawdown * 100 || 0).toFixed(2)}%</div>
              <div className="text-slate-400">Trades: {selectedVal.in_sample?.trades_count || 0}</div>
            </div>

            {/* Split 2 */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-slate-500 text-[10px] uppercase font-bold">2. Validation (25%)</span>
              <div className="text-slate-200">
                Return: <strong className="text-emerald-400">{(selectedVal.validation?.total_return * 100 || 0).toFixed(2)}%</strong>
              </div>
              <div className="text-slate-400">Max DD: {(selectedVal.validation?.max_drawdown * 100 || 0).toFixed(2)}%</div>
              <div className="text-slate-400">Profit Factor: {selectedVal.validation?.profit_factor || 0}</div>
            </div>

            {/* Split 3 */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
              <span className="text-slate-500 text-[10px] uppercase font-bold">3. Untouched Out-Of-Sample (25%)</span>
              <div className="text-slate-200">
                Return: <strong className={selectedVal.out_of_sample?.total_return > 0 ? 'text-emerald-400' : 'text-rose-400'}>
                  {(selectedVal.out_of_sample?.total_return * 100 || 0).toFixed(2)}%
                </strong>
              </div>
              <div className="text-slate-400">Max DD: {(selectedVal.out_of_sample?.max_drawdown * 100 || 0).toFixed(2)}%</div>
              <div className="text-slate-400">Stress 2x Cost Return: {(selectedVal.stress_test?.stress_oos_return * 100 || 0).toFixed(2)}%</div>
            </div>
          </div>

          {/* Walk-Forward & Regime Summary */}
          <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between text-slate-300 font-mono">
              <span>Walk-Forward Window Consistency:</span>
              <span className="font-bold text-amber-400">
                {((selectedVal.walk_forward?.consistency || 0) * 100).toFixed(0)}% ({selectedVal.walk_forward?.passing_windows}/{selectedVal.walk_forward?.total_windows} windows passed)
              </span>
            </div>
            {selectedVal.failure_reasons?.length > 0 && (
              <div className="mt-2 p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px] font-mono">
                <strong>Failure Factors:</strong> {selectedVal.failure_reasons.join(' • ')}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
