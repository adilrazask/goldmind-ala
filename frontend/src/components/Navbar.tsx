import React from 'react';
import { Activity, ShieldAlert, Cpu, Play, Pause, Square, TrendingUp, TrendingDown, Zap, Globe, Sparkles } from 'lucide-react';

interface NavbarProps {
  state: any;
  onControl: (action: string) => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ state, onControl }) => {
  const isKillSwitch = state?.kill_switch_active;
  const agentStatus = state?.agent_status || 'IDLE';
  const mode = state?.operating_mode || 'RESEARCH_ONLY';
  const account = state?.account || {};

  return (
    <header className="border-b border-amber-500/20 bg-slate-950/95 backdrop-blur-md sticky top-0 z-40">
      {/* Institutional Top Ticker Strip */}
      <div className="h-8 border-b border-slate-900 bg-slate-950 px-6 flex items-center justify-between text-[11px] font-mono text-slate-400 select-none overflow-x-auto">
        <div className="flex items-center gap-6 shrink-0">
          <div className="flex items-center gap-1.5 text-amber-400 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>MARKET TICKERS:</span>
          </div>
          
          <div className="flex items-center gap-1.5">
            <span className="text-slate-300 font-bold">XAUUSD</span>
            <span className="text-amber-400 font-bold">$2,684.50</span>
            <span className="text-emerald-400 flex items-center text-[10px]"><TrendingUp className="w-3 h-3 inline" />+0.82%</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-300 font-bold">BTCUSD</span>
            <span className="text-amber-400 font-bold">$91,420.00</span>
            <span className="text-emerald-400 flex items-center text-[10px]"><TrendingUp className="w-3 h-3 inline" />+2.45%</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-300 font-bold">ETHUSD</span>
            <span className="text-slate-200 font-bold">$3,412.00</span>
            <span className="text-emerald-400 flex items-center text-[10px]"><TrendingUp className="w-3 h-3 inline" />+1.65%</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-300 font-bold">DXY</span>
            <span className="text-slate-200">103.82</span>
            <span className="text-rose-400 flex items-center text-[10px]"><TrendingDown className="w-3 h-3 inline" />-0.18%</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-300 font-bold">US10Y</span>
            <span className="text-slate-200">4.18%</span>
            <span className="text-emerald-400 text-[10px]">+0.03</span>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            <Globe className="w-3 h-3" />
            <span>London / NY Overlap Session</span>
          </div>
          <div className="text-slate-500">
            Latency: <span className="text-slate-300 font-mono">1.2ms</span>
          </div>
        </div>
      </div>

      {/* Main Command Bar */}
      <div className="h-16 px-6 flex items-center justify-between">
        {/* Brand & Neural Brain Status */}
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-3">
            <div className="relative group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 via-amber-500 to-amber-700 flex items-center justify-center font-black text-slate-950 shadow-lg shadow-amber-500/25 ring-1 ring-amber-300/40">
                <Sparkles className="w-5 h-5 text-slate-950 fill-slate-950" />
              </div>
              <div className="absolute -inset-0.5 bg-amber-500/30 rounded-xl blur-sm -z-10 group-hover:bg-amber-400/40 transition" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-tight text-base gold-gradient-text uppercase">
                  GoldMind ALA
                </span>
                <span className="text-[10px] font-mono font-bold uppercase tracking-widest px-2 py-0.5 rounded bg-gradient-to-r from-amber-500/20 to-amber-600/10 text-amber-300 border border-amber-500/30">
                  AI QUANT LAB
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                Autonomous Learning Agent • 10-Family Strategy Engine
              </p>
            </div>
          </div>

          <div className="h-6 w-[1px] bg-slate-800 hidden sm:block" />

          {/* Autonomous Neural Pulse Badge */}
          <div className="hidden md:flex items-center gap-2.5">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
              agentStatus === 'RUNNING' 
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' 
                : agentStatus === 'PAUSED'
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                : 'bg-slate-900 text-slate-300 border-slate-800'
            }`}>
              <span className="relative flex h-2.5 w-2.5">
                {agentStatus === 'RUNNING' && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                )}
                <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                  agentStatus === 'RUNNING' ? 'bg-emerald-400' :
                  agentStatus === 'PAUSED' ? 'bg-amber-400' : 'bg-slate-500'
                }`} />
              </span>
              <span className="tracking-wide">AI BRAIN: {agentStatus}</span>
            </div>

            <div className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-slate-900/90 border border-slate-800 text-slate-300">
              <span className="text-slate-500">MODE:</span> <strong className="text-amber-400">{mode}</strong>
            </div>

            <div className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold uppercase border ${
              account.mode === 'REAL' 
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' 
                : 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30'
            }`}>
              {account.mode || 'GUARDED DEMO'}
            </div>
          </div>
        </div>

        {/* Account Telemetry & Control Actions */}
        <div className="flex items-center gap-4">
          {/* Equity & Margin Card */}
          <div className="hidden xl:flex items-center gap-5 text-xs font-mono px-3.5 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-inner">
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-sans font-semibold">Demo Equity</div>
              <div className="text-emerald-400 font-bold text-sm">
                ${(account.equity ?? 10000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div className="h-6 w-[1px] bg-slate-800" />
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-sans font-semibold">Daily Risk Util</div>
              <div className="text-amber-400 font-bold text-sm">
                0.25% <span className="text-[10px] text-slate-500 font-normal">/ 1.0%</span>
              </div>
            </div>
          </div>

          {/* Quick Engine Controls */}
          <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-800 rounded-xl p-1 shadow-sm">
            <button
              onClick={() => onControl('START')}
              title="Start continuous research cycles"
              className="px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/15 rounded-lg flex items-center gap-1.5 transition active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-emerald-400/20" /> Start Loop
            </button>
            <button
              onClick={() => onControl('PAUSE')}
              title="Pause task execution"
              className="px-3 py-1.5 text-xs font-semibold text-amber-400 hover:bg-amber-500/15 rounded-lg flex items-center gap-1.5 transition active:scale-95"
            >
              <Pause className="w-3.5 h-3.5 fill-amber-400/20" /> Pause
            </button>
            <button
              onClick={() => onControl('STOP')}
              title="Stop scheduler loop safely"
              className="px-3 py-1.5 text-xs font-semibold text-slate-400 hover:bg-slate-800 rounded-lg flex items-center gap-1.5 transition active:scale-95"
            >
              <Square className="w-3.5 h-3.5" /> Stop
            </button>
          </div>

          {/* Emergency Kill Switch Button */}
          <button
            onClick={() => onControl(isKillSwitch ? 'DEACTIVATE_KILL_SWITCH' : 'KILL_SWITCH')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition shadow-lg active:scale-95 ${
              isKillSwitch
                ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 animate-pulse ring-2 ring-amber-300'
                : 'bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white shadow-rose-900/40 ring-1 ring-rose-500/50'
            }`}
            title="Halts all order entries and invokes emergency risk policy immediately"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>{isKillSwitch ? 'RESET KILL SWITCH' : 'KILL SWITCH'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
