import React from 'react';
import {
  LayoutDashboard,
  Cpu,
  FlaskConical,
  Activity,
  LineChart,
  BookOpen,
  Radio,
  ShieldCheck,
  Database,
  Settings,
  Shield,
  Binary,
  Layers
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'agent'
  | 'strategies'
  | 'monitor'
  | 'backtest'
  | 'learning'
  | 'demo'
  | 'live'
  | 'market-data'
  | 'settings';

interface SidebarProps {
  activePage: PageId;
  onSelectPage: (id: PageId) => void;
  pendingValidationCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onSelectPage,
  pendingValidationCount = 0
}) => {
  const navSections = [
    {
      title: 'QUANTITATIVE RESEARCH',
      items: [
        { id: 'dashboard' as PageId, label: '1. Executive Terminal', icon: LayoutDashboard },
        { id: 'agent' as PageId, label: '2. AI Agent Workspace', icon: Cpu, badgeText: 'AI' },
        { id: 'strategies' as PageId, label: '3. Strategy Laboratory', icon: FlaskConical },
        { id: 'monitor' as PageId, label: '4. Research Monitor', icon: Activity },
        { id: 'backtest' as PageId, label: '5. Backtest & Validate', icon: LineChart, badge: pendingValidationCount },
      ]
    },
    {
      title: 'LEARNING & EXECUTION',
      items: [
        { id: 'learning' as PageId, label: '6. Learning Centre', icon: BookOpen },
        { id: 'demo' as PageId, label: '7. Demo Trading Desk', icon: Radio },
        { id: 'live' as PageId, label: '8. Live Risk Controls', icon: ShieldCheck, warning: true },
        { id: 'market-data' as PageId, label: '9. Market Feeds', icon: Database },
        { id: 'settings' as PageId, label: '10. Settings & Ops', icon: Settings },
      ]
    }
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950 flex flex-col justify-between shrink-0 h-[calc(100vh-6rem)] select-none">
      <div className="p-3 space-y-4 overflow-y-auto">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1">
            <div className="px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-widest text-slate-500 font-mono">
              {section.title}
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectPage(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all group relative ${
                    isActive
                      ? 'bg-gradient-to-r from-amber-500/15 to-transparent text-amber-300 font-bold border-l-4 border-amber-400 pl-2.5'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/60 border-l-4 border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 transition ${isActive ? 'text-amber-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                    <span className="tracking-tight">{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {item.badge}
                    </span>
                  )}
                  {item.badgeText && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-400/10 text-amber-300 border border-amber-400/20">
                      {item.badgeText}
                    </span>
                  )}
                  {item.warning && (
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-slate-800 text-slate-400">
                      LOCKED
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* System Telemetry Badges */}
      <div className="p-4 border-t border-slate-900 bg-slate-950/80 text-[11px] font-mono space-y-2">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5"><Binary className="w-3.5 h-3.5 text-amber-400" /> AST Sandbox</span>
          <span className="text-emerald-400 font-bold">VERIFIED</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-amber-400" /> Risk Engine</span>
          <span className="text-emerald-400 font-bold">18 CHECKS</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5"><Layers className="w-3.5 h-3.5 text-amber-400" /> Memory Tiers</span>
          <span className="text-amber-400 font-bold">5 TIERS</span>
        </div>
      </div>
    </aside>
  );
};
