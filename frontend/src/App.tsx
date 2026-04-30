import { useState, useEffect, useCallback } from "react";
import { fetchSnapshot, type Snapshot } from "./api/client";
import EpsilonCurve from "./components/EpsilonCurve";
import ImpliedDepreciation from "./components/ImpliedDepreciation";
import KeyNumbers from "./components/KeyNumbers";
import "./App.css";

type Status = "idle" | "loading" | "ok" | "error";

export default function App() {
  const [data, setData] = useState<Snapshot | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const snap = await fetchSnapshot();
      setData(snap);
      setLastRefresh(new Date());
      setStatus("ok");
    } catch (e: any) {
      setErrorMsg(e?.message ?? "Unknown error");
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const hasErrors = (data?.errors?.length ?? 0) > 0;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1 className="app-title">USD/TRY ε Dashboard</h1>
          <p className="app-subtitle">
            VIOP futures decomposition · CIP-implied vs market devaluation premium
          </p>
        </div>
        <div className="header-right">
          <button
            className="refresh-btn"
            onClick={load}
            disabled={status === "loading"}
          >
            {status === "loading" ? "Refreshing…" : "↻ Refresh"}
          </button>
          {lastRefresh && (
            <span className="last-refresh">
              Last: {lastRefresh.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      {hasErrors && (
        <div className="error-banner">
          <strong>Data warnings:</strong>
          <ul>
            {data!.errors.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      {status === "error" && (
        <div className="fatal-error">
          <strong>Cannot reach backend:</strong> {errorMsg}
          <br />
          <small>Make sure the FastAPI server is running on port 8000.</small>
        </div>
      )}

      {status === "loading" && !data && (
        <div className="loading-state">
          <div className="spinner" />
          Fetching live market data…
        </div>
      )}

      {data && (
        <main className="panels">
          <EpsilonCurve data={data.epsilon} />
          <ImpliedDepreciation data={data.epsilon} />
          <KeyNumbers
            market={data.market}
            epsilon={data.epsilon}
            viopContracts={data.viop_contracts}
            fetchedAt={data.fetched_at}
          />
        </main>
      )}

      <footer className="app-footer">
        Sources: VIOP via borsapy · Spot via yfinance · r_TRY{" "}
        {data?.market.r_try_source ?? "manual"} · r_USD{" "}
        {data?.market.r_usd_source ?? "—"} · Simple interest (CIP)
      </footer>
    </div>
  );
}
