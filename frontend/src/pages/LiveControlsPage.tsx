import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  Unlock,
  AlertOctagon,
  RotateCcw,
  KeyRound
} from 'lucide-react';
import { api } from '../api';

export const LiveControlsPage: React.FC = () => {
  const [controls, setControls] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [authPhrase, setAuthPhrase] = useState('');
  const [operatorName, setOperatorName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchControls = async () => {
    try {
      const res = await api.getLiveControls();
      setControls(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchControls();
  }, []);

  const handleAuthorize = async (enable: boolean) => {
    if (!operatorName.trim()) {
      alert('Operator name required for audit authentication.');
      return;
    }
    setSubmitting(true);
    try {
      await api.authorizeLive({
        enable,
        confirmation_phrase: authPhrase,
        authorized_by: operatorName,
        max_risk_per_trade: controls?.max_risk_per_trade_pct || 0.25,
        daily_loss_limit: controls?.daily_loss_limit_pct || 1.0
      });
      setAuthPhrase('');
      fetchControls();
      alert(`Live trading status updated: ${enable ? 'ENABLED' : 'REVOKED'}`);
    } catch (err: any) {
      alert(`Authorization failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center">Loading security protocols...</div>;
  }

  const isLive = controls?.live_trading_enabled;
  const isKill = controls?.kill_switch_active;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-500" />
            Live Trading Controls & Independent Authorization
          </h1>
          <p className="text-xs text-slate-400">
            Air-gapped security gate. Live execution is disabled by default and requires explicit cryptographic confirmation.
            The AI agent cannot authorize itself or modify safety caps.
          </p>
        </div>

        <button
          onClick={fetchControls}
          className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Security Status Banner */}
      <div className={`p-5 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
        isLive
          ? 'bg-rose-500/10 border-rose-500/40 text-rose-300'
          : 'bg-slate-900 border-slate-800 text-slate-300'
      }`}>
        <div className="space-y-1">
          <div className="flex items-center gap-2 font-bold text-sm">
            {isLive ? <Unlock className="w-4 h-4 text-rose-400" /> : <Lock className="w-4 h-4 text-emerald-400" />}
            Live Execution State: {isLive ? 'LIVE AUTHORIZED (REAL CAPITAL RISK)' : 'DISABLED BY DEFAULT (SAFE)'}
          </div>
          <p className="text-xs text-slate-400">
            {isLive
              ? 'Real-money orders are permitted for strictly allowlisted strategies that pass all pre-trade checks.'
              : 'Autonomous engine is restricted to local research and verified demo environments.'}
          </p>
        </div>

        {isLive && (
          <button
            onClick={() => handleAuthorize(false)}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-lg text-xs transition self-start"
          >
            Revoke Live Authorization Immediately
          </button>
        )}
      </div>

      {/* Safety Matrix Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Risk Enforcements */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-amber-400" /> Hardcoded Risk Limits
          </h3>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Max Risk Per Trade:</span>
              <span className="text-slate-200 font-bold">{controls?.max_risk_per_trade_pct}% of equity</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Daily Loss Hard Limit:</span>
              <span className="text-slate-200 font-bold">{controls?.daily_loss_limit_pct}%</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Max Open Positions:</span>
              <span className="text-slate-200 font-bold">{controls?.max_open_positions} positions</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-slate-400">Max Permitted Spread:</span>
              <span className="text-slate-200 font-bold">{controls?.max_spread_points} points</span>
            </div>
          </div>
        </div>

        {/* Authenticated Authorization Form */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <KeyRound className="w-4 h-4 text-amber-400" /> Explicit Owner Authorization
          </h3>

          <div className="text-xs text-slate-400 space-y-2">
            <p>
              To authorize live execution, enter the exact passphrase:
            </p>
            <div className="p-2 rounded bg-slate-950 border border-slate-800 font-mono text-amber-400 font-bold text-[11px]">
              {controls?.confirmation_phrase_required}
            </div>

            <div className="space-y-2 pt-2">
              <div>
                <label className="text-slate-500 text-[11px]">Operator Signature</label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  placeholder="e.g., Lead Architect / Portfolio Owner"
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono text-xs focus:outline-none"
                />
              </div>

              <div>
                <label className="text-slate-500 text-[11px]">Confirmation Phrase</label>
                <input
                  type="password"
                  value={authPhrase}
                  onChange={(e) => setAuthPhrase(e.target.value)}
                  placeholder="Paste exact phrase..."
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono text-xs focus:outline-none"
                />
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  disabled={submitting || !authPhrase || !operatorName}
                  onClick={() => handleAuthorize(true)}
                  className="flex-1 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-bold rounded text-xs transition"
                >
                  {submitting ? 'Authenticating...' : 'Authorize Live Trading'}
                </button>
                <button
                  type="button"
                  onClick={() => handleAuthorize(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded text-xs transition"
                >
                  Revoke
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
