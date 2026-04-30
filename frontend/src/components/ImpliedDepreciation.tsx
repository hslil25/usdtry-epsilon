import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { EpsilonTenor } from "../api/client";

interface Props {
  data: EpsilonTenor[];
}

const CORRIDOR_LOW = 18;
const CORRIDOR_HIGH = 20;

export default function ImpliedDepreciation({ data }: Props) {
  const chartData = data
    .filter((d) => d.dep_market_pct != null)
    .map((d) => ({
      tenor: d.tenor,
      market: d.dep_market_pct,
      cip: d.dep_cip_pct,
      extrapolated: d.extrapolated,
    }));

  return (
    <div className="panel">
      <h2 className="panel-title">Implied Annual Depreciation vs Corridor</h2>
      <p className="panel-sub">
        Market-implied depreciation vs CIP-implied &nbsp;|&nbsp;
        Grey band = 18–20% corridor pace
      </p>

      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="tenor" tick={{ fill: "#94a3b8", fontSize: 13 }} />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            tickFormatter={(v) => `${v.toFixed(0)}%`}
            label={{ value: "Ann. %", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11 }}
            domain={[0, "auto"]}
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value.toFixed(2)}%`,
              name === "market" ? "Market-implied" : "CIP-implied",
            ]}
            contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 6 }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Legend
            formatter={(v) => (v === "market" ? "Market-implied" : "CIP-implied")}
            wrapperStyle={{ color: "#94a3b8", fontSize: 12 }}
          />
          {/* Corridor reference band */}
          <ReferenceLine
            y={CORRIDOR_LOW}
            stroke="#64748b"
            strokeDasharray="6 3"
            label={{ value: "18%", position: "right", fill: "#64748b", fontSize: 10 }}
          />
          <ReferenceLine
            y={CORRIDOR_HIGH}
            stroke="#64748b"
            strokeDasharray="6 3"
            label={{ value: "20%", position: "right", fill: "#64748b", fontSize: 10 }}
          />
          <Bar dataKey="market" fill="#3b82f6" radius={[3, 3, 0, 0]} name="market" />
          <Bar dataKey="cip" fill="#10b981" radius={[3, 3, 0, 0]} name="cip" />
        </BarChart>
      </ResponsiveContainer>

      <div className="corridor-note">
        <span className="corridor-swatch" />
        <span>18–20% corridor pace (dashed lines) — reference only; not a forecast</span>
      </div>

      <div className="tenor-annotation-grid">
        {chartData.map((d) => (
          <div key={d.tenor} className="tenor-annotation">
            <span className="tenor-label">
              {d.tenor} {d.extrapolated && <span className="badge-ext">⚠ EXTRAP.</span>}
            </span>
            <span className="tenor-detail" style={{ color: "#3b82f6" }}>
              Mkt {d.market.toFixed(2)}%
            </span>
            <span className="tenor-detail" style={{ color: "#10b981" }}>
              CIP {d.cip.toFixed(2)}%
            </span>
            <span
              className="tenor-detail"
              style={{ color: d.market > CORRIDOR_HIGH ? "#f97316" : "#64748b" }}
            >
              {d.market > CORRIDOR_HIGH
                ? `+${(d.market - CORRIDOR_HIGH).toFixed(1)}% above corridor`
                : d.market < CORRIDOR_LOW
                ? `${(CORRIDOR_LOW - d.market).toFixed(1)}% below corridor`
                : "Within corridor"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
