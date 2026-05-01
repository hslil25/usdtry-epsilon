import {
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import type { MarketData } from "../api/client";

interface Props {
  market: MarketData;
}

const WEEKLY_TREND_PCT = 0.275;
const BAND_PCT = 0.05;

function trendStatus(actual: number | null) {
  if (actual == null) return { label: "—", color: "#64748b", detail: "" };
  const diff = actual - WEEKLY_TREND_PCT;
  if (Math.abs(diff) <= BAND_PCT)
    return {
      label: "IN TREND",
      color: "#22c55e",
      detail: `${actual >= 0 ? "+" : ""}${actual.toFixed(3)}% vs ${WEEKLY_TREND_PCT}% target`,
    };
  if (actual > WEEKLY_TREND_PCT)
    return {
      label: "ABOVE TREND",
      color: "#f97316",
      detail: `+${diff.toFixed(3)}% faster than ${WEEKLY_TREND_PCT}% target`,
    };
  return {
    label: actual < 0 ? "APPRECIATING" : "BELOW TREND",
    color: "#3b82f6",
    detail: `${diff.toFixed(3)}% vs ${WEEKLY_TREND_PCT}% target`,
  };
}

/** Exponential projection: compound weekly rate to monthly / annual */
function projectExponential(weeklyPct: number | null) {
  if (weeklyPct == null) return { monthly: null, annual: null };
  const w = weeklyPct / 100;
  // 365/7 = 52.143 weeks/year   365/7/12 = 4.345 weeks/month
  const monthly = ((1 + w) ** (365 / 7 / 12) - 1) * 100;
  const annual = ((1 + w) ** (365 / 7) - 1) * 100;
  return { monthly, annual };
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const close = payload.find((p: any) => p.dataKey === "close");
  const trend = payload.find((p: any) => p.dataKey === "trend");
  return (
    <div className="tooltip-box">
      <p style={{ color: "#94a3b8", fontSize: "0.68rem", marginBottom: 4 }}>{label}</p>
      {close && (
        <p style={{ color: close.color }}>
          Spot <strong>{close.value.toFixed(4)}</strong>
        </p>
      )}
      {trend && (
        <p style={{ color: "#64748b" }}>
          Corridor <strong>{trend.value.toFixed(4)}</strong>
        </p>
      )}
    </div>
  );
};

export default function SpotTrend({ market }: Props) {
  const { spot, spot_history, weekly_change_pct } = market;
  const status = trendStatus(weekly_change_pct);
  const { monthly, annual } = projectExponential(weekly_change_pct);

  const history = spot_history ?? [];
  const firstClose = history[0]?.close ?? spot ?? 0;
  const chartData = history.map((d, i) => {
    const t = i / Math.max(history.length - 1, 1);
    return {
      date: d.date.slice(5),
      close: d.close,
      trend: parseFloat((firstClose * (1 + (WEEKLY_TREND_PCT / 100) * t)).toFixed(4)),
    };
  });

  const closes = history.map((d) => d.close);
  const trends = chartData.map((d) => d.trend);
  const allVals = [...closes, ...trends];
  const yMin = allVals.length ? Math.min(...allVals) * 0.9995 : 0;
  const yMax = allVals.length ? Math.max(...allVals) * 1.0005 : 1;

  return (
    <div className="spot-trend-panel">
      {/* Left column */}
      <div className="st-left">
        <div className="st-label">USD / TRY</div>
        <div className="st-spot">{spot?.toFixed(4) ?? "—"}</div>

        <div className="st-weekly-row">
          <span className="st-weekly-val" style={{ color: status.color }}>
            {weekly_change_pct != null
              ? `${weekly_change_pct >= 0 ? "+" : ""}${weekly_change_pct.toFixed(3)}%`
              : "—"}
          </span>
          <span className="st-weekly-sub">7-day change</span>
        </div>

        <div
          className="st-trend-badge"
          style={{
            background: status.color + "18",
            color: status.color,
            border: `1px solid ${status.color}44`,
          }}
        >
          {status.label}
        </div>
        <div className="st-trend-detail">{status.detail}</div>

        {/* Exponential projections */}
        <div className="st-proj-grid">
          <div className="st-proj-card">
            <div className="st-proj-label">Monthly implied</div>
            <div className="st-proj-val" style={{ color: status.color }}>
              {monthly != null ? `${monthly >= 0 ? "+" : ""}${monthly.toFixed(2)}%` : "—"}
            </div>
            <div className="st-proj-sub">exp. compounded</div>
          </div>
          <div className="st-proj-card">
            <div className="st-proj-label">Annual implied</div>
            <div className="st-proj-val" style={{ color: status.color }}>
              {annual != null ? `${annual >= 0 ? "+" : ""}${annual.toFixed(1)}%` : "—"}
            </div>
            <div className="st-proj-sub">exp. compounded</div>
          </div>
        </div>

        <div className="st-benchmark">Benchmark: {WEEKLY_TREND_PCT}% / week</div>
      </div>

      {/* Right column: 7-day chart */}
      <div className="st-right">
        <div className="st-chart-label">
          — Actual &nbsp;&nbsp;
          <span style={{ color: "#475569" }}>-- {WEEKLY_TREND_PCT}% / wk pace</span>
        </div>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="spotGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={status.color} stopOpacity={0.2} />
                <stop offset="95%" stopColor={status.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis
              domain={[yMin, yMax]}
              tick={{ fill: "#475569", fontSize: 10 }}
              tickFormatter={(v) => v.toFixed(2)}
              axisLine={false}
              tickLine={false}
              width={48}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              dataKey="trend"
              stroke="#475569"
              strokeDasharray="4 3"
              strokeWidth={1}
              dot={false}
              isAnimationActive={false}
            />
            <Area
              dataKey="close"
              stroke={status.color}
              strokeWidth={2}
              fill="url(#spotGrad)"
              dot={{ fill: status.color, r: 2, strokeWidth: 0 }}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
