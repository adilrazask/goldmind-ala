import React, { useState } from 'react';

interface ChartPoint {
  timestamp: string;
  equity?: number;
  drawdown?: number;
  value?: number;
}

interface SimpleChartProps {
  data: ChartPoint[];
  valueKey?: 'equity' | 'drawdown' | 'value';
  color?: string;
  fillColor?: string;
  height?: number;
  label?: string;
  isPercentage?: boolean;
}

export const SimpleChart: React.FC<SimpleChartProps> = ({
  data,
  valueKey = 'equity',
  color = '#f59e0b',
  fillColor = 'url(#goldGradient)',
  height = 200,
  label = 'Performance',
  isPercentage = false
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!data || data.length < 2) {
    return (
      <div
        style={{ height }}
        className="w-full flex flex-col items-center justify-center bg-slate-900/40 rounded-xl border border-slate-800/80 text-xs text-slate-500 gap-2 p-6"
      >
        <div className="w-8 h-8 rounded-full border-2 border-amber-500/20 border-t-amber-400 animate-spin" />
        <span>Synthesizing continuous backtest equity telemetry...</span>
      </div>
    );
  }

  const values = data.map((d) => (d[valueKey] !== undefined ? d[valueKey]! : 0));
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal === 0 ? 1 : maxVal - minVal;

  const width = 800;
  const paddingX = 40;
  const paddingTop = 25;
  const paddingBottom = 30;
  const chartW = width - paddingX * 2;
  const chartH = height - paddingTop - paddingBottom;

  const points = values.map((val, idx) => {
    const x = paddingX + (idx / (values.length - 1)) * chartW;
    const y = paddingTop + chartH - ((val - minVal) / range) * chartH;
    return { x, y, val, timestamp: data[idx]?.timestamp || `T+${idx}` };
  });

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const areaD = `${pathD} L ${(paddingX + chartW).toFixed(1)},${(paddingTop + chartH).toFixed(1)} L ${paddingX.toFixed(1)},${(paddingTop + chartH).toFixed(1)} Z`;

  const maxIndex = values.indexOf(maxVal);
  const peakPoint = points[maxIndex];

  const activePoint = hoverIndex !== null && hoverIndex >= 0 && hoverIndex < points.length ? points[hoverIndex] : points[points.length - 1];

  // Grid line levels
  const gridLevels = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div className="w-full bg-slate-900/80 rounded-xl border border-slate-800 p-4 shadow-xl">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">{label}</span>
          <span className="text-[10px] text-slate-500 font-mono">({values.length} observations)</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs font-mono">
            <span className="text-slate-500 mr-1.5">{hoverIndex !== null ? 'Cursor:' : 'Latest:'}</span>
            <span className="font-bold text-amber-400 text-sm">
              {isPercentage ? `${(activePoint.val * 100).toFixed(2)}%` : `$${activePoint.val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
            </span>
          </div>
        </div>
      </div>

      <div className="relative">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible select-none"
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const relX = (e.clientX - rect.left) / rect.width;
            const targetX = relX * width;
            // find closest point
            let closest = 0;
            let minDist = 999999;
            points.forEach((p, idx) => {
              const d = Math.abs(p.x - targetX);
              if (d < minDist) {
                minDist = d;
                closest = idx;
              }
            });
            setHoverIndex(closest);
          }}
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.35" />
              <stop offset="70%" stopColor="#f59e0b" stopOpacity="0.05" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="glow" />
              <feComposite in="SourceGraphic" in2="glow" operator="over" />
            </filter>
          </defs>

          {/* Grid lines */}
          {gridLevels.map((lvl) => {
            const y = paddingTop + chartH - lvl * chartH;
            const gridVal = minVal + lvl * range;
            return (
              <g key={lvl}>
                <line
                  x1={paddingX}
                  y1={y}
                  x2={paddingX + chartW}
                  y2={y}
                  stroke="#1e293b"
                  strokeDasharray="3 3"
                  strokeWidth="1"
                />
                <text
                  x={paddingX - 6}
                  y={y + 3}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="9"
                  fontFamily="monospace"
                >
                  {isPercentage ? `${(gridVal * 100).toFixed(1)}%` : gridVal > 999 ? `$${(gridVal / 1000).toFixed(1)}k` : `$${gridVal.toFixed(0)}`}
                </text>
              </g>
            );
          })}

          {/* Area fill */}
          <path d={areaD} fill={fillColor} />

          {/* Main Curve Line */}
          <path
            d={pathD}
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#glow)"
          />

          {/* Peak High-Water Mark Indicator */}
          {peakPoint && (
            <g>
              <circle cx={peakPoint.x} cy={peakPoint.y} r="4" fill="#f59e0b" stroke="#fff" strokeWidth="1.5" />
              <rect
                x={Math.min(peakPoint.x - 30, width - paddingX - 60)}
                y={Math.max(peakPoint.y - 20, 2)}
                width="60"
                height="14"
                rx="3"
                fill="#0f172a"
                stroke="#f59e0b"
                strokeWidth="1"
              />
              <text
                x={Math.min(peakPoint.x, width - paddingX - 30)}
                y={Math.max(peakPoint.y - 10, 12)}
                textAnchor="middle"
                fill="#fef08a"
                fontSize="8"
                fontFamily="monospace"
                fontWeight="bold"
              >
                PEAK {isPercentage ? `${(maxVal * 100).toFixed(1)}%` : `$${maxVal.toFixed(0)}`}
              </text>
            </g>
          )}

          {/* Hover Crosshair */}
          {hoverIndex !== null && activePoint && (
            <g>
              <line
                x1={activePoint.x}
                y1={paddingTop}
                x2={activePoint.x}
                y2={paddingTop + chartH}
                stroke="#f59e0b"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              <circle
                cx={activePoint.x}
                cy={activePoint.y}
                r="5"
                fill="#f59e0b"
                stroke="#030712"
                strokeWidth="2"
              />
            </g>
          )}
        </svg>
      </div>

      <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 mt-2 px-2">
        <span>Inception ({data[0]?.timestamp || 'T=0'})</span>
        <span>Latest Sample ({data[data.length - 1]?.timestamp || 'T+N'})</span>
      </div>
    </div>
  );
};
