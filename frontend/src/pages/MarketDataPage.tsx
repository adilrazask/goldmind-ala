import React, { useState, useEffect } from 'react';
import {
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  FileSpreadsheet,
  Upload,
  Layers,
  Clock
} from 'lucide-react';
import { api } from '../api';

export const MarketDataPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const res = await api.getMarketDataHealth();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center">Checking data feed health...</div>;
  }

  const providers = data?.providers || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-amber-400" />
            Market Data Quality & Feed Architecture
          </h1>
          <p className="text-xs text-slate-400">
            Real-time feed provenance, missing candle auditing, duplicate timestamp rejection, and historical CSV ingestion.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Provider Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {providers.map((p: any) => {
          const health = p.health || {};
          return (
            <div
              key={p.symbol}
              className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 text-xs font-mono"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 font-sans">
                <div>
                  <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    {p.symbol} <span className="text-xs font-mono font-normal text-slate-400">({p.timeframe})</span>
                  </h3>
                  <span className="text-xs text-slate-400">{p.name}</span>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-[11px] font-bold flex items-center gap-1 ${
                    health.is_valid
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                  }`}
                >
                  {health.is_valid ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                  {health.is_valid ? 'FEED VERIFIED' : 'DATA ANOMALY'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-slate-300">
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-500 text-[10px] uppercase">Total Bars Audited</span>
                  <div className="text-sm font-bold text-slate-100">{health.total_candles}</div>
                </div>
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-500 text-[10px] uppercase">Missing Candles</span>
                  <div className="text-sm font-bold text-slate-100">{health.missing_candles}</div>
                </div>
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-500 text-[10px] uppercase">Duplicate Bars</span>
                  <div className="text-sm font-bold text-slate-100">{health.duplicate_candles}</div>
                </div>
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-500 text-[10px] uppercase">Invalid OHLC Bars</span>
                  <div className="text-sm font-bold text-slate-100">{health.invalid_ohlc_bars}</div>
                </div>
              </div>

              <div className="space-y-1 text-[11px] text-slate-400 pt-1">
                <div>Start: {health.start_time || 'N/A'}</div>
                <div>End: {health.end_time || 'N/A'}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Historical CSV Ingestion Banner */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 text-xs">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 font-sans">
          <FileSpreadsheet className="w-4 h-4 text-amber-400" /> Historical CSV Dataset Ingestion
        </h3>
        <p className="text-slate-400">
          The market data manager imports custom CSV files containing{' '}
          <code className="text-amber-300 font-mono">timestamp,open,high,low,close,volume</code> columns.
          All timestamps are parsed into UTC, audited for strict chronological sorting, and checked for high/low continuity before candidate generation.
        </p>
        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-400">
          CLI Import Utility: <span className="text-amber-400">python3 main.py backtest --csv /path/to/XAUUSD_M15.csv</span>
        </div>
      </div>
    </div>
  );
};
