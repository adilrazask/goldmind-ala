import React, { useState, useEffect } from 'react';
import {
  Radio,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  Send,
  RotateCcw,
  DollarSign,
  AlertTriangle
} from 'lucide-react';
import { api } from '../api';

export const DemoTradingPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [symbol, setSymbol] = useState('XAUUSD');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [riskPercent, setRiskPercent] = useState(0.25);
  const [slPoints, setSlPoints] = useState(300);
  const [tpPoints, setTpPoints] = useState(600);
  const [submitting, setSubmitting] = useState(false);

  const fetchDemo = async () => {
    try {
      const res = await api.getDemoAccount();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDemo();
    const interval = setInterval(fetchDemo, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.submitDemoTrade({
        strategy_id: 'DEMO_MANUAL_EXEC',
        symbol,
        side,
        risk_percent: riskPercent,
        sl_points: slPoints,
        tp_points: tpPoints
      });
      fetchDemo();
    } catch (err: any) {
      alert(`Order rejected: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = async (ticket: number) => {
    if (!confirm(`Confirm closing position #${ticket}?`)) return;
    try {
      await api.closeDemoPosition(ticket);
      fetchDemo();
    } catch (err: any) {
      alert(`Could not close: ${err.message}`);
    }
  };

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center">Connecting to demo broker gateway...</div>;
  }

  const account = data?.account || {};
  const positions = data?.positions || [];
  const orders = data?.recent_orders || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Radio className="w-5 h-5 text-amber-400" />
            Verified Demo Execution Terminal
          </h1>
          <p className="text-xs text-slate-400">
            Guarded execution sandbox. All order entries require mandatory risk validation, SL presence, and margin checks.
          </p>
        </div>

        {/* Verified Account Mode Pill */}
        <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          VERIFIED BROKER MODE: {account.mode || 'DEMO'}
        </span>
      </div>

      {/* Account Financials Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-500">Broker Session</span>
          <div className="text-sm font-bold text-slate-100 truncate">{account.broker}</div>
          <div className="text-[11px] font-mono text-slate-400">Acc: {account.account_number}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-500">Live Equity</span>
          <div className="text-lg font-bold font-mono text-emerald-400">
            ${account.equity?.toLocaleString()}
          </div>
          <div className="text-[11px] font-mono text-slate-400">Balance: ${account.balance?.toLocaleString()}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-500">Free Margin</span>
          <div className="text-lg font-bold font-mono text-slate-100">
            ${account.free_margin?.toLocaleString()}
          </div>
          <div className="text-[11px] font-mono text-slate-400">Used: ${account.margin?.toLocaleString()}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-500">Active Positions</span>
          <div className="text-lg font-bold font-mono text-amber-400">
            {positions.length} / 3 Max
          </div>
          <div className="text-[11px] font-mono text-slate-400">Automated Risk Capped</div>
        </div>
      </div>

      {/* Order Entry Form & Open Positions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Guarded Order Entry */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-amber-400" /> Pre-Trade Risk Gate Order
            </h3>
          </div>

          <form onSubmit={handleOrder} className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400">Instrument</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
              >
                <option value="XAUUSD">XAUUSD (Gold Spot)</option>
                <option value="BTCUSD">BTCUSD (Bitcoin)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-slate-400">Side</label>
                <select
                  value={side}
                  onChange={(e) => setSide(e.target.value as any)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
                >
                  <option value="buy">BUY</option>
                  <option value="sell">SELL</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400">Risk % (Max 0.25%)</label>
                <input
                  type="number"
                  step="0.05"
                  max="0.25"
                  value={riskPercent}
                  onChange={(e) => setRiskPercent(parseFloat(e.target.value))}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-slate-400">SL Points</label>
                <input
                  type="number"
                  value={slPoints}
                  onChange={(e) => setSlPoints(parseInt(e.target.value))}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400">TP Points</label>
                <input
                  type="number"
                  value={tpPoints}
                  onChange={(e) => setTpPoints(parseInt(e.target.value))}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold rounded transition flex items-center justify-center gap-1.5 mt-2"
            >
              <Send className="w-3.5 h-3.5" />
              {submitting ? 'Checking Risk Gate...' : 'Submit Risk-Gated Order'}
            </button>
          </form>
        </div>

        {/* Open Positions Table */}
        <div className="lg:col-span-2 p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Open Broker Positions ({positions.length})
          </h3>

          <div className="overflow-x-auto">
            {positions.length > 0 ? (
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-800">
                    <th className="py-2">Ticket</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Volume</th>
                    <th>Open Price</th>
                    <th>SL / TP</th>
                    <th>Profit</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {positions.map((p: any) => (
                    <tr key={p.ticket}>
                      <td className="py-2.5 font-bold">{p.ticket}</td>
                      <td className="text-slate-200 font-bold">{p.symbol}</td>
                      <td>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          p.side === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                        }`}>
                          {p.side}
                        </span>
                      </td>
                      <td>{p.volume}</td>
                      <td>{p.open_price}</td>
                      <td className="text-slate-400 text-[11px]">
                        {p.stop_loss} / {p.take_profit}
                      </td>
                      <td className={p.unrealized_profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                        ${p.unrealized_profit?.toFixed(2)}
                      </td>
                      <td>
                        <button
                          onClick={() => handleClose(p.ticket)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-rose-500/20 hover:text-rose-300 text-slate-300 transition text-[11px]"
                        >
                          Close
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="py-12 text-center text-xs text-slate-500">
                No active demo positions on broker.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Order State History & Risk Rejections */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Order State Lifecycle & Risk Rejections ({orders.length})
        </h3>
        <div className="overflow-x-auto max-h-60 overflow-y-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-500 border-b border-slate-800">
                <th className="py-2">Time</th>
                <th>Order ID</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Volume</th>
                <th>State</th>
                <th>Details / Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {orders.map((o: any) => (
                <tr key={o.id}>
                  <td className="py-2 text-slate-500">{new Date(o.created_at).toLocaleTimeString()}</td>
                  <td className="text-slate-300">{o.id.slice(0, 10)}...</td>
                  <td>{o.symbol}</td>
                  <td>{o.side}</td>
                  <td>{o.volume}</td>
                  <td>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      o.state === 'FILLED' ? 'bg-emerald-500/10 text-emerald-400' :
                      o.state === 'REJECTED' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {o.state}
                    </span>
                  </td>
                  <td className="text-slate-400 text-[11px] truncate max-w-xs">
                    {o.rejection_reason || `Broker Ticket #${o.ticket}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
