import React, { useState, useEffect } from 'react';
import {
  Activity,
  Layers,
  Clock,
  Terminal,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Cpu
} from 'lucide-react';
import { api } from '../api';

export const ResearchMonitorPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchMonitor = async () => {
    try {
      const res = await api.getResearchMonitor();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitor();
    const interval = setInterval(fetchMonitor, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center">Loading research monitor...</div>;
  }

  const currentObj = data?.current_objective;
  const currentTask = data?.current_task;
  const events = data?.event_timeline || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-amber-400" />
            Live Research Monitor
          </h1>
          <p className="text-xs text-slate-400">
            Real-time auditable task execution timeline, resource consumption telemetry, and dataset tracking.
          </p>
        </div>

        <button
          onClick={fetchMonitor}
          className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition"
          title="Refresh monitor"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Current Objective & Active Execution Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Active Objective */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs">
          <div className="text-slate-500 font-medium uppercase tracking-wider text-[10px]">
            Target Research Scope
          </div>
          <div className="font-bold text-sm text-slate-100">
            {currentObj?.title || 'No active objective.'}
          </div>
          <p className="text-slate-400 font-mono text-[11px]">
            Objective ID: {currentObj?.id || 'None'}
          </p>
          {currentObj?.intent && (
            <div className="flex items-center gap-2 text-amber-400 font-mono">
              <span>{currentObj.intent.instrument}</span> • <span>{currentObj.intent.timeframe}</span> • <span>{currentObj.intent.target_family}</span>
            </div>
          )}
        </div>

        {/* Current Task Telemetry */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs">
          <div className="text-slate-500 font-medium uppercase tracking-wider text-[10px]">
            Active Research Task
          </div>
          {currentTask ? (
            <div className="space-y-1">
              <div className="font-bold text-emerald-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                {currentTask.type}
              </div>
              <div className="font-mono text-slate-400 text-[11px]">Task ID: {currentTask.id}</div>
              <div className="font-mono text-slate-400 text-[11px]">
                Budget: Max Memory {currentTask.budget?.max_memory_mb}MB, Timeout {currentTask.budget?.timeout_seconds}s
              </div>
            </div>
          ) : (
            <div className="text-slate-500 py-3">
              Task queue idle. Scheduler awaiting next interval cycle.
            </div>
          )}
        </div>
      </div>

      {/* Event Timeline */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Terminal className="w-4 h-4 text-amber-400" /> Auditable Research Event Stream ({events.length})
        </h3>

        <div className="space-y-2 max-h-[500px] overflow-y-auto font-mono text-xs">
          {events.length > 0 ? (
            events.map((ev: any) => {
              const isError = ev.type === 'ERROR';
              return (
                <div
                  key={ev.id}
                  className={`p-3 rounded-lg border text-xs flex items-start justify-between gap-4 ${
                    isError
                      ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                      : 'bg-slate-950 border-slate-800/80 text-slate-300'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded uppercase ${
                        isError ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-amber-400'
                      }`}>
                        {ev.type}
                      </span>
                      <span className="text-[11px] text-slate-500">{ev.task_id}</span>
                    </div>
                    <div className="text-slate-200">{ev.message}</div>
                  </div>
                  <div className="text-[10px] text-slate-500 whitespace-nowrap">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No events recorded yet. Run a research task to generate auditable execution logs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
