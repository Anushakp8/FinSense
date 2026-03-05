export interface StockListItem {
  ticker: string;
  latest_price: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

export interface TechnicalIndicators {
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  bollinger_upper: number | null;
  bollinger_lower: number | null;
  sma_50: number | null;
  sma_200: number | null;
}

export interface StockDetail {
  ticker: string;
  latest_price: number;
  change_pct: number;
  previous_close: number;
  volume: number;
  timestamp: string;
  technical_indicators: TechnicalIndicators | null;
}

export interface StockHistoryItem {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PredictionResponse {
  ticker: string;
  direction: "UP" | "DOWN";
  confidence: number;
  model_version: string;
  model_name: string;
  timestamp: string;
}

export interface IndividualRisk {
  ticker: string;
  weight: number;
  annual_volatility: number;
  var_95: number;
  expected_return: number;
}

export interface PortfolioRiskResponse {
  var_95: number;
  var_99: number;
  expected_return: number;
  max_drawdown: number;
  annual_volatility: number;
  individual_risks: IndividualRisk[];
}

export interface PipelineStatus {
  status: "healthy" | "degraded" | "failed";
  last_data_update: string | null;
  data_freshness_hours: number | null;
  row_counts: Record<string, number>;
  active_model: Record<string, unknown> | null;
  message: string;
}
