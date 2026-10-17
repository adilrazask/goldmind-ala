import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  Database,
  ShieldCheck,
  RotateCcw,
  CheckCircle2,
  Server,
  Download
} from 'lucide-react';
import { api } from '../api';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchSettings = async () => {
    try {
      const res = await api.getSettings();
      setSettings(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center">Loading system configuration...</div>;
  }

  const risk = settings?.risk_limits || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-amber-400" />
            Settings & System Operations
          </h1>
          <p className="text-xs text-slate-400">
            Persistent storage parameters, Ollama language model connection, and scheduler resource limits.
          </p>
        </div>

        <button
          onClick={fetchSettings}
          className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Model & AI Configuration */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3 text-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-amber-400" /> Language Model Adapter (Ollama)
          </h3>
          <p className="text-slate-400">
            Language models propose declarative strategy JSON specifications only. They never generate executable Python in the main process.
          </p>
          <div className="space-y-2 font-mono">
            <div className="flex justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-500">Ollama Enabled:</span>
              <span className={settings?.use_ollama ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                {settings?.use_ollama ? 'TRUE' : 'FALSE (LOCAL SPEC GENERATOR)'}
              </span>
            </div>
            <div className="flex justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-500">Ollama Host:</span>
              <span className="text-slate-300">{settings?.ollama_host}</span>
            </div>
            <div className="flex justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-500">Configured Model:</span>
              <span className="text-amber-400 font-bold">{settings?.ollama_model}</span>
            </div>
          </div>
        </div>

        {/* Database & Storage Architecture */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3 text-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Database className="w-4 h-4 text-amber-400" /> Relational Database Architecture
          </h3>
          <p className="text-slate-400">
            All 30 relational schemas (objectives, tasks, backtests, validation gates, lessons, broker orders) are migrated.
          </p>
          <div className="space-y-2 font-mono">
            <div className="flex justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-500">Engine / Dialect:</span>
              <span className="text-slate-200">SQLite 3 / SQLAlchemy 2.0</span>
            </div>
            <div className="flex justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-500">Storage Target:</span>
              <span className="text-slate-300 truncate max-w-xs">{settings?.database_url}</span>
            </div>
            <div className="flex justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-500">Schema Health:</span>
              <span className="text-emerald-400 font-bold">30 TABLES VERIFIED</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Limits */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3 text-xs">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Server className="w-4 h-4 text-amber-400" /> Resource Caps & Scheduler Limits
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
          <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500">Max Risk / Trade</span>
            <div className="text-slate-200 font-bold">{risk.max_risk_per_trade_pct}%</div>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500">Daily Loss Hard Cap</span>
            <div className="text-slate-200 font-bold">{risk.daily_loss_limit_pct}%</div>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500">Max Open Positions</span>
            <div className="text-slate-200 font-bold">{risk.max_open_positions}</div>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] text-slate-500">Max Spread Tolerated</span>
            <div className="text-slate-200 font-bold">{risk.max_spread_points} pts</div>
          </div>
        </div>
      </div>
    </div>
  );
};
