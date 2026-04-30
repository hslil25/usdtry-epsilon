import type { EpsilonTenor, MarketData, ViopContract } from "../api/client";

interface Props {
  market: MarketData;
  epsilon: EpsilonTenor[];
  viopContracts: ViopContract[];
  fetchedAt: string;
}

function SignalBadge({ signal, eps }: { signal: string; eps: number }) {
  const color =
    eps < 0 ? "#3b82f6"
    : signal === "neutral" ? "#6b7280"
    : signal === "break-premium" ? "#f97316"
    : "#ef4444";

  const label =
    eps < 0 ? "compression"
    : signal === "neutral" ? "neutral"
    : signal === "break-premium" ? "break-premium"
    : "acute-stress";

  return (
    <span className="signal-badge" style={{ background: color + "22", color, border: `1px solid ${color}55` }}>
      {label}
    </span>
  );
}

function SourceTag({ source }: { source: string }) {
  const isManual = source?.includes("manual") || source?.includes("fallback");
  return (
    <span className={`source-tag ${isManual ? "source-manual" : "source-live"}`}>
      {isManual ? "manual" : "live"}
    </span>
  );
}

function fmt(n: number | null | undefined, decimals = 4): string {
  if (n == null) return "—";
  return n.toFixed(decimals);
}

function fmtPct(n: number | null | undefined): string {
  if (n == null) return "—";
  return `${(n * 100).toFixed(2)}%`;
}

export default function KeyNumbers({ market, epsilon, viopContracts, fetchedAt }: Props) {
  const ts = new Date(fetchedAt);
  const tsLocal = ts.toLocaleString();

  return (
    <div className="panel">
      <h2 className="panel-title">Key Numbers</h2>

      {/* Rates block */}
      <div className="kn-grid">
        <div className="kn-card">
          <div className="kn-label">USD/TRY Spot</div>
          <div className="kn-value">{fmt(market.spot, 4)}</div>
          <SourceTag source={market.spot_source} />
        </div>
        <div className="kn-card">
          <div className="kn-label">r_TRY (CBRT)</div>
          <div className="kn-value">{fmtPct(market.r_try)}</div>
          <SourceTag source={market.r_try_source} />
        </div>
        <div className="kn-card">
          <div className="kn-label">r_USD (Fed)</div>
          <div className="kn-value">{fmtPct(market.r_usd)}</div>
          <SourceTag source={market.r_usd_source} />
        </div>
        <div className="kn-card">
          <div className="kn-label">Interest Differential</div>
          <div className="kn-value">{fmtPct(market.interest_differential)}</div>
          <span className="source-tag source-computed">computed</span>
        </div>
      </div>

      {/* ε per tenor */}
      <h3 className="section-title">ε by Tenor</h3>
      <div className="eps-table">
        <div className="eps-row eps-header">
          <span>Tenor</span>
          <span>Days</span>
          <span>F actual</span>
          <span>F CIP</span>
          <span>ε</span>
          <span>Signal</span>
        </div>
        {epsilon.map((d) => (
          <div key={d.tenor} className="eps-row">
            <span className="eps-tenor">
              {d.tenor}
              {d.extrapolated && <span className="badge-ext ml-1">⚠</span>}
            </span>
            <span>{d.days}</span>
            <span>{fmt(d.f_actual, 3)}</span>
            <span>{fmt(d.f_theoretical, 3)}</span>
            <span style={{ color: d.epsilon < 0 ? "#3b82f6" : d.epsilon > 0.5 ? "#ef4444" : "#f97316" }}>
              {d.epsilon >= 0 ? "+" : ""}{fmt(d.epsilon, 4)}
            </span>
            <span>
              {d.signal ? <SignalBadge signal={d.signal} eps={d.epsilon} /> : "—"}
            </span>
          </div>
        ))}
      </div>

      {/* Raw VIOP contracts */}
      <h3 className="section-title">Raw VIOP Contracts Used</h3>
      <div className="contracts-table">
        <div className="ctr-row ctr-header">
          <span>Symbol</span>
          <span>Price</span>
          <span>Expiry</span>
          <span>Days</span>
        </div>
        {viopContracts.map((c) => (
          <div key={c.symbol} className="ctr-row">
            <span className="ctr-symbol">{c.symbol}</span>
            <span>{c.price.toFixed(4)}</span>
            <span>{c.expiry}</span>
            <span>{c.days_to_expiry}</span>
          </div>
        ))}
      </div>

      {/* Freshness */}
      <div className="freshness">
        <span className="freshness-dot" />
        Data as of: {tsLocal}
      </div>
    </div>
  );
}
