const BASE_URL = '/api/v1';

export async function fetchApi(endpoint: string, options?: RequestInit) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    },
    ...options
  });
  if (!res.ok) {
    let errorDetail = 'API Request Failed';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Page 1: Dashboard
  getDashboardState: () => fetchApi('/dashboard/state'),
  controlDashboard: (action: string, intervalSeconds: number = 60) =>
    fetchApi(`/dashboard/controls?action=${action}&interval_seconds=${intervalSeconds}`, { method: 'POST' }),

  // Page 2: Agent Workspace
  getObjectives: () => fetchApi('/agent/objectives'),
  createObjective: (rawPrompt: string, title?: string) =>
    fetchApi('/agent/objective', {
      method: 'POST',
      body: JSON.stringify({ raw_prompt: rawPrompt, title: title || '' })
    }),
  stepAgent: () => fetchApi('/agent/step', { method: 'POST' }),

  // Page 3: Strategy Lab
  getStrategies: (family?: string) =>
    fetchApi(`/strategies${family ? `?family=${family}` : ''}`),
  generateBatch: (family: string, count: number = 5) =>
    fetchApi(`/strategies/generate-batch?family=${family}&count=${count}`, { method: 'POST' }),

  // Page 4: Research Monitor
  getResearchMonitor: () => fetchApi('/research/monitor'),

  // Page 5: Backtesting & Validation
  getBacktestResults: () => fetchApi('/backtest/results'),
  getValidationResults: () => fetchApi('/validation/results'),

  // Page 6: Learning Centre
  getLearningMemory: () => fetchApi('/learning/memory'),
  addInstruction: (instruction: string, category: string = 'GENERAL') =>
    fetchApi('/learning/instruction', {
      method: 'POST',
      body: JSON.stringify({ instruction, category })
    }),
  addExample: (title: string, exampleDecision: string, explanation: string, feedbackLabel: string) =>
    fetchApi('/learning/example', {
      method: 'POST',
      body: JSON.stringify({ title, example_decision: exampleDecision, explanation, feedback_label: feedbackLabel })
    }),
  submitFeedback: (lessonId: string, feedback: string, notes?: string) =>
    fetchApi('/learning/feedback', {
      method: 'POST',
      body: JSON.stringify({ lesson_id: lessonId, feedback, notes })
    }),

  // Page 7: Demo Trading
  getDemoAccount: () => fetchApi('/demo/account'),
  submitDemoTrade: (order: { strategy_id: string; symbol: string; side: string; risk_percent?: number; sl_points?: number; tp_points?: number }) =>
    fetchApi('/demo/trade', {
      method: 'POST',
      body: JSON.stringify(order)
    }),
  closeDemoPosition: (ticket: number) =>
    fetchApi(`/demo/close-position?ticket=${ticket}`, { method: 'POST' }),

  // Page 8: Live Controls
  getLiveControls: () => fetchApi('/live/controls'),
  authorizeLive: (payload: { enable: boolean; confirmation_phrase: string; authorized_by: string; max_risk_per_trade: number; daily_loss_limit: number }) =>
    fetchApi('/live/authorize', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  toggleKillSwitch: (active: boolean, reason: string) =>
    fetchApi('/live/kill-switch', {
      method: 'POST',
      body: JSON.stringify({ active, reason, actor: 'UI_OPERATOR' })
    }),

  // Page 9: Market Data
  getMarketDataHealth: () => fetchApi('/market-data/health'),

  // Page 10: Settings
  getSettings: () => fetchApi('/settings')
};
