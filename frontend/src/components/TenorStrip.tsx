import type { ContractEpsilon } from "../api/client";

interface Props {
  data: ContractEpsilon[];
  spot: number | null;
  weeklyChangePct: number | null;
}

const SIG_COLOR: Record<string, string> = {
  compression:    "#3b82f6",
  neutral:        "#6b7280",
  "break-premium":"#f97316",
  "acute-stress": "#ef4444",
};

const SIG_LABEL: Record<string, string> = {
  compression:    "compress.",
  neutral:        "neutral",
  "break-premium":"break+",
  "acute-stress": "stress!",
};

function daysLabel(days: number): string {
  if (days < 30) return `${days}d`;
  if (days < 365) return `${Math.round(days / 30)}M`;
  return `${(days / 365).toFixed(1)}Y`;
}

/** Spot × (1 + weeklyRate)^(days/7) — exponential projection of current weekly pace */
function weeklyTrendForward(spot: number, weeklyPct: number, days: number): number {
  const w = weeklyPct / 100;
  return spot * Math.pow(1 + w, days / 7);
}

export default function TenorStrip({ data, spot, weeklyChangePct }: Props) {
  if (!data?.length) return null;

  const maxEps = Math.max(...data.map((d) => Math.abs(d.epsilon)), 0.01);
  const showTrend = spot != null && weeklyChangePct != null;

  return (
    <div className="panel tenor-strip-panel">
      <h2 className="panel-title">ε Across All Contracts</h2>
      <p className="panel-sub">
        Each card = one live VIOP contract &nbsp;·&nbsp;
        ε = F<sub>act</sub> − F<sub>CIP</sub> &nbsp;·&nbsp;
        <span style={{ color: "#a78bfa" }}>■ trend</span> = weekly pace extrapolated
      </p>

      <div className="ts-grid">
        {data.map((d) => {
          const color = SIG_COLOR[d.signal] ?? "#6b7280";
          const barW = Math.abs(d.epsilon) / maxEps;
          const isNeg = d.epsilon < 0;

          const fTrend = showTrend
            ? weeklyTrendForward(spot!, weeklyChangePct!, d.days)
            : null;

          // How far market is from weekly-trend-implied price
          const trendDiff = fTrend != null ? d.f_actual - fTrend : null;

          return (
            <div key={d.symbol} className="ts-card">
              {/* Tenor + code */}
              <div className="ts-days">{daysLabel(d.days)}</div>
              <div className="ts-symbol">
                {d.symbol.replace("F_USDTRY", "").replace("TM_F_USDTRY", "TM·")}
              </div>

              {/* Three price lines */}
              <div className="ts-prices">
                <div className="ts-price-row">
                  <span className="ts-price-dot" style={{ background: "#94a3b8" }} />
                  <span className="ts-price-label">Mkt</span>
                  <span className="ts-price-val">{d.f_actual.toFixed(3)}</span>
                </div>
                <div className="ts-price-row">
                  <span className="ts-price-dot" style={{ background: "#10b981" }} />
                  <span className="ts-price-label">CIP</span>
                  <span className="ts-price-val" style={{ color: "#64748b" }}>
                    {d.f_theoretical.toFixed(3)}
                  </span>
                </div>
                {fTrend != null && (
                  <div className="ts-price-row">
                    <span className="ts-price-dot" style={{ background: "#a78bfa" }} />
                    <span className="ts-price-label">Trnd</span>
                    <span className="ts-price-val" style={{ color: "#a78bfa" }}>
                      {fTrend.toFixed(3)}
                    </span>
                  </div>
                )}
              </div>

              {/* ε bar (market vs CIP) */}
              <div className="ts-bar-section">
                <div className="ts-bar-label">vs CIP</div>
                <div className="ts-bar-track">
                  <div
                    className="ts-bar-fill"
                    style={{
                      width: `${barW * 100}%`,
                      background: color,
                      marginLeft: isNeg ? "auto" : undefined,
                    }}
                  />
                </div>
                <div className="ts-eps" style={{ color }}>
                  {d.epsilon >= 0 ? "+" : ""}{d.epsilon.toFixed(3)}
                </div>
              </div>

              {/* vs weekly trend */}
              {trendDiff != null && (
                <div className="ts-bar-section">
                  <div className="ts-bar-label">vs trend</div>
                  <div className="ts-bar-track">
                    <div
                      className="ts-bar-fill"
                      style={{
                        width: `${Math.min(Math.abs(trendDiff) / maxEps, 1) * 100}%`,
                        background: "#a78bfa",
                        marginLeft: trendDiff < 0 ? "auto" : undefined,
                        opacity: 0.7,
                      }}
                    />
                  </div>
                  <div className="ts-eps" style={{ color: "#a78bfa" }}>
                    {trendDiff >= 0 ? "+" : ""}{trendDiff.toFixed(3)}
                  </div>
                </div>
              )}

              {/* Signal badge */}
              <div
                className="ts-signal"
                style={{
                  background: color + "18",
                  color,
                  border: `1px solid ${color}44`,
                }}
              >
                {SIG_LABEL[d.signal] ?? d.signal}
              </div>

              {/* Ann. depreciation */}
              <div className="ts-dep">
                <span style={{ color: "#94a3b8" }}>{d.dep_market_pct.toFixed(1)}%</span>
                <span className="ts-dep-sep">/</span>
                <span style={{ color: "#10b981" }}>{d.dep_cip_pct.toFixed(1)}%</span>
              </div>
              <div className="ts-dep-label">ann. mkt / CIP</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
