import React, { useState, useEffect } from 'react';
import {
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  FileSpreadsheet,
  Globe,
  Radio,
  Zap,
  TrendingUp
} from 'lucide-react';
import { api } from '../api';

export const MarketDataPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [deltaStatus, setDeltaStatus] = useState<any>(null);
  const [deltaTickers, setDeltaTickers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [resHealth, resDelta, resTickers] = await Promise.all([
        api.getMarketDataHealth(),
        api.getDeltaStatus().catch(() => null),
        api.getDeltaTickers().catch(() => ({ tickers: [] }))
      ]);
      setData(resHealth);
      setDeltaStatus(resDelta);
      setDeltaTickers(resTickers?.tickers || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 8000);
    return () => clearInterval(timer);
  }, []);

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center font-mono">Checking data feed health & Delta Exchange streams...</div>;
  }

  const providers = data?.providers || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-amber-400" />
            Market Data Quality & Delta Exchange Streams
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            Delta Exchange official REST v2 & WebSocket feeds • Missing candle audits • Stale-data detection
          </p>
        </div>

        <button
          onClick={fetchData}
          className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition flex items-center gap-1.5 text-xs font-mono"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Delta Exchange Live Connection Card */}
      {deltaStatus && (
        <div className="p-5 rounded-xl bg-slate-900/90 border border-cyan-500/30 shadow-lg space-y-4 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center border border-cyan-500/30">
                <Globe className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <span>Delta Exchange Official Gateway</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                    {deltaStatus.configuration?.environment || 'INDIA_TESTNET'}
                  </span>
                </h3>
                <span className="text-[11px] text-slate-400">
                  REST: {deltaStatus.rest?.endpoint} • Latency: {deltaStatus.rest?.latency_ms || 0}ms
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold flex items-center gap-1.5 ${
                deltaStatus.status === 'ONLINE'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              }`}>
                <Radio className={`w-3.5 h-3.5 ${deltaStatus.status === 'ONLINE' ? 'animate-pulse' : ''}`} />
                {deltaStatus.status === 'ONLINE' ? 'EXCHANGE ONLINE' : 'DISCONNECTED'}
              </span>

              <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold ${
                deltaStatus.websocket?.data_freshness_status === 'FRESH'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
              }`}>
                WS: {deltaStatus.websocket?.data_freshness_status || 'IDLE'}
              </span>
            </div>
          </div>

          {/* Delta Real-time Tickers Grid */}
          <div className="space-y-2">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
              Real-time Exchange Tickers
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {deltaTickers.length > 0 ? (
                deltaTickers.slice(0, 4).map((t: any) => (
                  <div key={t.symbol} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-slate-400">
                      <span className="font-bold text-slate-200">{t.symbol}</span>
                      <span className="text-[10px] text-emerald-400">Live</span>
                    </div>
                    <div className="text-base font-bold text-slate-100">${t.close.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                    <div className="flex justify-between text-[10px] text-slate-500">
                      <span>Bid: ${t.bid}</span>
                      <span>Ask: ${t.ask}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="col-span-4 p-3 rounded-lg bg-slate-950 border border-slate-800 text-slate-500 text-center text-[11px]">
                  Connecting to Delta Exchange public ticker feeds ({deltaStatus.configuration?.environment})...
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Internal & Simulated Provider Health Cards */}
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
