import React, { useState } from 'react';
import {
  Send,
  Cpu,
  Layers,
  CheckCircle2,
  Clock,
  Play,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  Zap,
  HelpCircle,
  FileText,
  Binary
} from 'lucide-react';
import { api } from '../api';

interface AgentWorkspacePageProps {
  objectives: any[];
  onRefresh: () => void;
  onStepAgent: () => void;
}

export const AgentWorkspacePage: React.FC<AgentWorkspacePageProps> = ({
  objectives,
  onRefresh,
  onStepAgent
}) => {
  const [prompt, setPrompt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [selectedObjectiveId, setSelectedObjectiveId] = useState<string | null>(
    objectives.length > 0 ? objectives[0].id : null
  );

  const samplePrompts = [
    {
      title: 'XAUUSD Volatility Filter',
      text: 'Investigate whether an ATR volatility filter improves M15 XAUUSD breakout strategies and conduct walk-forward validation.'
    },
    {
      title: 'BTCUSD Multi-Timeframe',
      text: 'Research BTCUSD momentum using 1H trend alignment and 15M pullback entries. Test across 4 market regimes.'
    },
    {
      title: 'EURUSD Mean Reversion',
      text: 'Formulate an RSI mean-reversion hypothesis for EURUSD with strict time-of-day filter during Asian session.'
    },
    {
      title: 'Cross-Asset Volatility Adaptation',
      text: 'Generate and validate an adaptive ATR-based trailing stop strategy on XAUUSD and assess 2x slippage resilience.'
    }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setSubmitting(true);
    try {
      const res = await api.createObjective(prompt);
      setPrompt('');
      onRefresh();
      if (res.objective_id) {
        setSelectedObjectiveId(res.objective_id);
      }
    } catch (err: any) {
      alert(`Error creating research objective: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const currentObj = objectives.find((o) => o.id === selectedObjectiveId) || objectives[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-white flex items-center gap-2 tracking-tight">
            <Cpu className="w-6 h-6 text-amber-400" />
            <span className="gold-gradient-text">Autonomous AI Agent Workspace</span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Formulate natural-language quantitative instructions. The agent parses intent, provisions memory, and executes sandbox-verified tasks.
          </p>
        </div>

        <button
          onClick={onStepAgent}
          className="px-4 py-2.5 text-xs font-bold bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 text-slate-950 rounded-xl flex items-center gap-2 transition shadow-lg shadow-amber-500/20 active:scale-95 self-start"
        >
          <Zap className="w-4 h-4 fill-slate-950" />
          <span>Execute Next Task</span>
        </button>
      </div>

      {/* Input Formulation Card */}
      <div className="p-6 rounded-2xl glass-card-gold space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 font-mono">
            <Sparkles className="w-4 h-4" />
            <span>Formulate Research Objective</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            Natural Language ➔ AST Sandbox Pipeline
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Research whether an ATR volatility expansion filter improves M15 XAUUSD breakout strategies during London/NY overlap..."
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-4 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400/80 resize-none font-sans shadow-inner"
            />
          </div>

          {/* Sample Prompts Pills */}
          <div className="space-y-1.5">
            <div className="text-[10px] font-mono uppercase text-slate-500 font-bold">Suggested Quantitative Directives:</div>
            <div className="flex flex-wrap gap-2">
              {samplePrompts.map((sp, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => setPrompt(sp.text)}
                  className="px-3 py-1 rounded-lg text-[11px] bg-slate-900/90 hover:bg-amber-500/10 hover:border-amber-500/40 border border-slate-800 text-slate-300 hover:text-amber-300 transition text-left"
                >
                  {sp.title}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
            <div className="text-[11px] text-slate-400 flex items-center gap-2 font-mono">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Causality Sandbox & Deterministic Risk Guard Active</span>
            </div>
            <button
              type="submit"
              disabled={submitting || !prompt.trim()}
              className="px-5 py-2.5 text-xs font-bold bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 rounded-xl flex items-center gap-2 transition shadow-md active:scale-95"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{submitting ? 'Decomposing Plan...' : 'Dispatch to Agent'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Persistent Objectives & Task Execution View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Objective Selector */}
        <div className="p-5 rounded-2xl glass-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              Research History ({objectives.length})
            </h3>
            <span className="text-[10px] font-mono text-amber-400">Persistent</span>
          </div>

          <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
            {objectives.length > 0 ? (
              objectives.map((obj) => (
                <button
                  key={obj.id}
                  onClick={() => setSelectedObjectiveId(obj.id)}
                  className={`w-full text-left p-3.5 rounded-xl border text-xs transition space-y-2 ${
                    currentObj?.id === obj.id
                      ? 'bg-gradient-to-r from-amber-500/15 to-transparent border-amber-500/40 text-amber-200 shadow-md'
                      : 'bg-slate-950/70 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold truncate text-slate-100">{obj.title || 'Quantitative Study'}</span>
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded ${
                      obj.status === 'COMPLETED' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {obj.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 font-sans">{obj.raw_prompt}</p>
                  <div className="text-[10px] font-mono text-slate-500 flex items-center justify-between pt-1 border-t border-slate-900">
                    <span>{obj.tasks?.length || 0} Tasks Decomposed</span>
                    <span className="text-amber-400/80">{obj.id.slice(0, 8)}</span>
                  </div>
                </button>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-500">
                No past objectives stored. Submit a research prompt to initialize the agent task graph.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Research Plan & Decomposed Task Queue */}
        <div className="lg:col-span-2 p-6 rounded-2xl glass-card space-y-5">
          {currentObj ? (
            <>
              <div className="border-b border-slate-800/80 pb-4 space-y-2">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-bold text-slate-100 font-mono">{currentObj.title}</h2>
                  <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded border border-amber-500/20">
                    {currentObj.id}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-slate-400">
                  <span>Instrument: <strong className="text-amber-300">{currentObj.parsed_intent?.instrument || 'XAUUSD'}</strong></span>
                  <span>•</span>
                  <span>Timeframe: <strong className="text-amber-300">{currentObj.parsed_intent?.timeframe || 'M15'}</strong></span>
                  <span>•</span>
                  <span>Target Family: <strong className="text-amber-300">{currentObj.parsed_intent?.target_family || 'breakout'}</strong></span>
                </div>
              </div>

              {/* Task Breakdown */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 font-mono">
                    <Layers className="w-4 h-4 text-amber-400" />
                    <span>Decomposed Task Queue ({currentObj.tasks?.length || 0} Steps)</span>
                  </h3>
                  <span className="text-[11px] font-mono text-slate-400">Execution Mode: Sandboxed</span>
                </div>

                <div className="space-y-3">
                  {currentObj.tasks?.map((task: any, idx: number) => {
                    const isDone = task.status === 'COMPLETED';
                    const isRunning = task.status === 'RUNNING';
                    return (
                      <div
                        key={task.task_id}
                        className={`p-4 rounded-xl border text-xs space-y-2.5 transition ${
                          isDone
                            ? 'bg-slate-950/80 border-emerald-500/30 shadow-sm'
                            : isRunning
                            ? 'bg-amber-500/10 border-amber-500/50 shadow-md animate-pulse'
                            : 'bg-slate-950/60 border-slate-800/80 text-slate-400'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold flex items-center gap-2.5 text-slate-200">
                            <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-mono font-bold ${
                              isDone ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-amber-400'
                            }`}>
                              {idx + 1}
                            </span>
                            <span className="font-mono">{task.type}</span>
                          </span>
                          <span className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold ${
                            isDone ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' :
                            isRunning ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                            'bg-slate-800 text-slate-400'
                          }`}>
                            {task.status}
                          </span>
                        </div>

                        {task.output && (
                          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1.5 overflow-hidden">
                            <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                              Output Telemetry & Evidence:
                            </div>
                            <pre className="text-slate-300 overflow-x-auto whitespace-pre-wrap text-[10px] max-h-36 bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
                              {JSON.stringify(task.output, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="py-16 text-center text-xs text-slate-500 space-y-3">
              <Cpu className="w-10 h-10 text-amber-500/30 mx-auto" />
              <div>Select an objective from the left or enter a new quantitative directive above.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
