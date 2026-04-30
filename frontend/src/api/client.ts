export interface BracketContract {
  symbol: string;
  price: number;
  days: number;
}

export interface EpsilonTenor {
  tenor: string;
  days: number;
  f_actual: number;
  f_theoretical: number;
  epsilon: number;
  signal: "compression" | "neutral" | "break-premium" | "acute-stress";
  dep_market_pct: number;
  dep_cip_pct: number;
  extrapolated: boolean;
  bracket: BracketContract[];
  error?: string;
}

export interface ViopContract {
  symbol: string;
  price: number;
  expiry: string;
  days_to_expiry: number;
}

export interface MarketData {
  spot: number | null;
  spot_source: string;
  r_try: number | null;
  r_try_source: string;
  r_usd: number | null;
  r_usd_source: string;
  interest_differential: number | null;
}

export interface Snapshot {
  fetched_at: string;
  market: MarketData;
  epsilon: EpsilonTenor[];
  viop_contracts: ViopContract[];
  errors: string[];
  viop_error: string | null;
}

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function fetchSnapshot(): Promise<Snapshot> {
  const r = await fetch(`${BASE}/snapshot`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
