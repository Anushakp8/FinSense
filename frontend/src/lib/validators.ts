import { z } from "zod/v4";

export const StockListItemSchema = z.object({
  ticker: z.string(),
  latest_price: z.number(),
  change_pct: z.number(),
  volume: z.number(),
  timestamp: z.string(),
});

export const StockListResponseSchema = z.object({
  stocks: z.array(StockListItemSchema),
  count: z.number(),
});

export const PredictionResponseSchema = z.object({
  ticker: z.string(),
  direction: z.enum(["UP", "DOWN"]),
  confidence: z.number(),
  model_version: z.string(),
  model_name: z.string(),
  timestamp: z.string(),
});

export const PipelineStatusSchema = z.object({
  status: z.enum(["healthy", "degraded", "failed"]),
  last_data_update: z.string().nullable(),
  data_freshness_hours: z.number().nullable(),
  row_counts: z.record(z.string(), z.number()),
  active_model: z.record(z.string(), z.unknown()).nullable(),
  message: z.string(),
});

export type StockListItem = z.infer<typeof StockListItemSchema>;
export type StockListResponse = z.infer<typeof StockListResponseSchema>;
export type PredictionResponse = z.infer<typeof PredictionResponseSchema>;
export type PipelineStatus = z.infer<typeof PipelineStatusSchema>;
