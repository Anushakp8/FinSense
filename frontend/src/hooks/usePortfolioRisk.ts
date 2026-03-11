import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import type { PortfolioRiskResponse } from "@/types";

export function usePortfolioRisk(tickers: string[], weights: number[]) {
  const tickerStr = tickers.join(",");
  const weightStr = weights.join(",");
  return useQuery({
    queryKey: ["portfolioRisk", tickerStr, weightStr],
    queryFn: async () => {
      const { data } = await apiClient.get<PortfolioRiskResponse>(
        `/api/v1/portfolio-risk?tickers=${tickerStr}&weights=${weightStr}`
      );
      return data;
    },
    enabled: tickers.length > 0 && weights.length > 0,
  });
}
