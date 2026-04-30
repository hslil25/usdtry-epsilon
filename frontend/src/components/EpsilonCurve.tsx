import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
  ResponsiveContainer,
} from "recharts";
import type { EpsilonTenor } from "../api/client";

interface Props {
  data: EpsilonTenor[];
}

function signalColor(signal: string, eps: number): string {
  if (eps < 0) return "#3b82f6";          // blue — compression
  if (signal === "neutral") return "#6b7280";  // gray
  if (signal === "break-premium") return "#f97316"; // orange
  return "#ef4444";                        // red — acute stress
}

function signalLabel(signal: string): string {
  switch (signal) {
    case "compression": return "Carry Compression";
    case "neutral": return "Neutral";
    case "break-premium": return "Break Premium";
    case "acute-stress": return "Acute Stress";
    default: return signal;
  }
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const d: EpsilonTenor = payload[0].payload;
  return (
    <div className="tooltip-box">
      <p className="tooltip-title">{label} {d.extrapolated && <span className="badge-ext">EXTRAPOLATED</span>}</p>
      <p>ε = <strong>{d.epsilon?.toFixed(4)}</strong> TRY</p>
      <p>F actual = {d.f_actual?.toFixed(4)}</p>
      <p>F theoretical = {d.f_theoretical?.toFixed(4)}</p>
      <p>Signal: <span style={{ color: signalColor(d.signal, d.epsilon) }}>{signalLabel(d.signal)}</span></p>
    </div>
  );
};

export default function EpsilonCurve({ data }: Props) {
  const chartData = data.filter((d) => d.epsilon != null);

  return (
    <div className="panel">
      <h2 className="panel-title">ε Curve — Devaluation Premium by Tenor</h2>
      <p className="panel-sub">
        ε = F<sub>actual</sub> − F<sub>CIP</sub> &nbsp;|&nbsp;
        <span style={{ color: "#3b82f6" }}>■ negative</span> =&nbsp;compression &nbsp;
        <span style={{ color: "#f97316" }}>■ orange</span> = break-premium &nbsp;
        <span style={{ color: "#ef4444" }}>■ red</span> = acute stress
      </p>

      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="tenor" tick={{ fill: "#94a3b8", fontSize: 13 }} />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            tickFormatter={(v) => v.toFixed(2)}
            label={{ value: "ε (TRY)", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 11 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="#475569" strokeWidth={1.5} />
          <Bar dataKey="epsilon" radius={[3, 3, 0, 0]}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={signalColor(entry.signal, entry.epsilon)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Per-bar annotations */}
      <div className="tenor-annotation-grid">
        {chartData.map((d) => (
          <div key={d.tenor} className="tenor-annotation">
            <span className="tenor-label">
              {d.tenor} {d.extrapolated && <span className="badge-ext">⚠ EXTRAPOLATED</span>}
            </span>
            <span className="tenor-detail">F<sub>act</sub> {d.f_actual?.toFixed(3)}</span>
            <span className="tenor-detail">F<sub>cip</sub> {d.f_theoretical?.toFixed(3)}</span>
            <span className="tenor-eps" style={{ color: signalColor(d.signal, d.epsilon) }}>
              ε {d.epsilon >= 0 ? "+" : ""}{d.epsilon?.toFixed(4)}
            </span>
            <span className="tenor-signal" style={{ color: signalColor(d.signal, d.epsilon) }}>
              {signalLabel(d.signal)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
