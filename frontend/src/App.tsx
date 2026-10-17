import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, PageId } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { AgentWorkspacePage } from './pages/AgentWorkspacePage';
import { StrategyLabPage } from './pages/StrategyLabPage';
import { ResearchMonitorPage } from './pages/ResearchMonitorPage';
import { BacktestPage } from './pages/BacktestPage';
import { LearningCenterPage } from './pages/LearningCenterPage';
import { DemoTradingPage } from './pages/DemoTradingPage';
import { LiveControlsPage } from './pages/LiveControlsPage';
import { MarketDataPage } from './pages/MarketDataPage';
import { SettingsPage } from './pages/SettingsPage';
import { api } from './api';
import { AlertTriangle, Wifi, WifiOff } from 'lucide-react';

const INITIAL_FALLBACK_STATE = {
  agent_status: 'IDLE',
  operating_mode: 'RESEARCH_ONLY',
  kill_switch_active: false,
  current_objective: 'Investigate whether volatility filters and multi-timeframe momentum enhance XAUUSD and BTCUSD strategy candidates.',
  experiments_count: 14,
  validated_strategies_count: 3,
  awaiting_validation_count: 2,
  rejected_strategies_count: 5,
  account: {
    equity: 10240.50,
    balance: 10000.00,
    free_margin: 9780.00,
    mode: 'DEMO'
  },
  scheduler: {
    is_running: false,
    interval_seconds: 60,
    cycle_count: 3
  },
  open_positions: [],
  equity_curve: [
    { timestamp: '09:00', equity: 10000.00 },
    { timestamp: '10:30', equity: 10045.20 },
    { timestamp: '12:00', equity: 10025.10 },
    { timestamp: '13:45', equity: 10115.50 },
    { timestamp: '15:15', equity: 10090.80 },
    { timestamp: '16:30', equity: 10185.40 },
    { timestamp: '18:00', equity: 10240.50 }
  ]
};

export function App() {
  const [activePage, setActivePage] = useState<PageId>('dashboard');
  const [dashboardState, setDashboardState] = useState<any>(INITIAL_FALLBACK_STATE);
  const [objectives, setObjectives] = useState<any[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(true);

  const fetchGlobalData = async () => {
    try {
      const [dash, objs, strats] = await Promise.all([
        api.getDashboardState(),
        api.getObjectives(),
        api.getStrategies()
      ]);
      setDashboardState(dash);
      setObjectives(objs);
      setStrategies(strats);
      setErrorMsg(null);
      setIsConnected(true);
    } catch (e: any) {
      setErrorMsg(e.message);
      setIsConnected(false);
    }
  };

  useEffect(() => {
    fetchGlobalData();
    const interval = setInterval(fetchGlobalData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleControl = async (action: string) => {
    try {
      await api.controlDashboard(action);
      fetchGlobalData();
    } catch (err: any) {
      alert(`Action error: ${err.message}`);
    }
  };

  const handleStepAgent = async () => {
    try {
      const res = await api.stepAgent();
      fetchGlobalData();
      if (res.executed_task) {
        // success notification
      } else {
        alert('All planned tasks for active objective are completed or queue is idle.');
      }
    } catch (err: any) {
      alert(`Step failed: ${err.message}`);
    }
  };

  return (
    <div className={`min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans ${theme}`}>
      <Navbar
        state={dashboardState}
        onControl={handleControl}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      />

      {/* Sleek Connectivity Status if Daemon is reconnecting */}
      {!isConnected && (
        <div className="bg-amber-950/60 border-b border-amber-800/60 text-amber-300 px-6 py-2 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2">
            <WifiOff className="w-4 h-4 text-amber-400 animate-pulse" />
            <span>ALA Daemon Offline ({errorMsg || 'Connection error'}). Operating with interactive local telemetry. Start backend server: <code>python3 main.py server --port 8000</code></span>
          </div>
          <button
            onClick={fetchGlobalData}
            className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/30 font-bold"
          >
            Reconnect
          </button>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activePage={activePage}
          onSelectPage={setActivePage}
          pendingValidationCount={dashboardState?.awaiting_validation_count || 0}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-slate-950/60">
          <div className="max-w-7xl mx-auto">
            {activePage === 'dashboard' && (
              <DashboardPage
                state={dashboardState}
                onControl={handleControl}
                onStepAgent={handleStepAgent}
                onNavigate={setActivePage}
              />
            )}
            {activePage === 'agent' && (
              <AgentWorkspacePage
                objectives={objectives}
                onRefresh={fetchGlobalData}
                onStepAgent={handleStepAgent}
              />
            )}
            {activePage === 'strategies' && (
              <StrategyLabPage
                strategies={strategies}
                onRefresh={fetchGlobalData}
                onNavigate={setActivePage}
              />
            )}
            {activePage === 'monitor' && <ResearchMonitorPage />}
            {activePage === 'backtest' && <BacktestPage />}
            {activePage === 'learning' && <LearningCenterPage />}
            {activePage === 'demo' && <DemoTradingPage />}
            {activePage === 'live' && <LiveControlsPage />}
            {activePage === 'market-data' && <MarketDataPage />}
            {activePage === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
