import React, { useState } from 'react';
import {
  FlaskConical,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Code,
  ShieldCheck,
  Play
} from 'lucide-react';
import { api } from '../api';

interface StrategyLabPageProps {
  strategies: any[];
  onRefresh: () => void;
  onNavigate: (page: any) => void;
}

const FAMILIES = [
  'ALL',
  'moving_average_crossover',
  'momentum',
  'breakout',
  'rsi_mean_reversion',
  'volatility_filtered',
  'trend_following',
  'multi_timeframe_confirmation',
  'atr_volatility_adaptation',
  'session_based',
  'composite_combination'
];

export const StrategyLabPage: React.FC<StrategyLabPageProps> = ({
  strategies,
  onRefresh,
  onNavigate
}) => {
  const [selectedFamily, setSelectedFamily] = useState('ALL');
  const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null);
  const [generating, setGenerating] = useState(false);

  const filteredStrategies = strategies.filter(
    (s) => selectedFamily === 'ALL' || s.family === selectedFamily
  );

  const handleGenerateBatch = async () => {
    setGenerating(true);
    try {
      const targetFamily = selectedFamily === 'ALL' ? 'momentum' : selectedFamily;
      await api.generateBatch(targetFamily, 5);
      onRefresh();
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-amber-400" />
            Strategy Generation Laboratory
          </h1>
          <p className="text-xs text-slate-400">
            Declarative candidate library across 10 allowlisted quantitative families.
            Candidates pass AST static safety, sandbox causality, and multi-stage statistical gates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerateBatch}
            disabled={generating}
            className="px-4 py-2 text-xs font-semibold bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 rounded-lg flex items-center gap-1.5 transition shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {generating ? 'Generating Spec...' : 'Generate New Candidates'}
          </button>
        </div>
      </div>

      {/* Family Filter Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2">
        {FAMILIES.map((fam) => (
          <button
            key={fam}
            onClick={() => setSelectedFamily(fam)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap transition ${
              selectedFamily === fam
                ? 'bg-amber-500 text-slate-950 font-bold'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            {fam.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Main Grid: Strategies Table & Spec Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Candidates Table */}
        <div className="lg:col-span-2 p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Registered Candidates ({filteredStrategies.length})
            </span>
          </div>

          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="text-slate-500 border-b border-slate-800">
                  <th className="py-2.5">Candidate ID</th>
                  <th>Family</th>
                  <th>Symbol</th>
                  <th>Timeframe</th>
                  <th>Status</th>
                  <th>Approval</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredStrategies.map((cand) => (
                  <tr
                    key={cand.candidate_id}
                    onClick={() => setSelectedCandidate(cand)}
                    className={`cursor-pointer transition hover:bg-slate-800/40 ${
                      selectedCandidate?.candidate_id === cand.candidate_id ? 'bg-amber-500/10' : ''
                    }`}
                  >
                    <td className="py-3 font-semibold text-slate-200">{cand.candidate_id}</td>
                    <td className="text-amber-400 font-medium">{cand.family}</td>
                    <td className="text-slate-300">{cand.instrument}</td>
                    <td className="text-slate-400">{cand.timeframe}</td>
                    <td>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          cand.status === 'PROMOTED_TO_DEMO'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : cand.status === 'SYNTAX_PASSED'
                            ? 'bg-indigo-500/10 text-indigo-400'
                            : 'bg-rose-500/10 text-rose-400'
                        }`}
                      >
                        {cand.status}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          cand.approval_state === 'DEMO_APPROVED'
                            ? 'bg-emerald-500/20 text-emerald-300 font-bold'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {cand.approval_state}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Deep Spec Inspector */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Code className="w-4 h-4 text-amber-400" /> Declarative Specification
            </span>
          </div>

          {selectedCandidate ? (
            <div className="space-y-3 text-xs">
              <div>
                <div className="text-slate-500 text-[11px]">Hypothesis:</div>
                <div className="text-slate-200 mt-1 italic bg-slate-950 p-2.5 rounded border border-slate-800">
                  "{selectedCandidate.hypothesis || 'Statistical hypothesis not recorded.'}"
                </div>
              </div>

              <div>
                <div className="text-slate-500 text-[11px]">Parameter Configuration:</div>
                <pre className="mt-1 bg-slate-950 p-3 rounded border border-slate-800 text-amber-300 font-mono text-[11px] overflow-x-auto">
                  {JSON.stringify(selectedCandidate.parameters, null, 2)}
                </pre>
              </div>

              <div>
                <div className="text-slate-500 text-[11px]">Full Declarative JSON Spec:</div>
                <pre className="mt-1 bg-slate-950 p-3 rounded border border-slate-800 text-slate-300 font-mono text-[11px] max-h-48 overflow-y-auto">
                  {JSON.stringify(selectedCandidate.spec_json, null, 2)}
                </pre>
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  onClick={() => onNavigate('backtest')}
                  className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-semibold transition"
                >
                  View Backtest Trajectory
                </button>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-xs text-slate-500">
              Select a strategy candidate from the list to inspect its parameter rules, sandbox status, and hypothesis.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
