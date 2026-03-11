import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import type { StockListItem, StockDetail, StockHistoryItem } from "@/types";

export function useStocks() {
  return useQuery({
    queryKey: ["stocks"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ stocks: StockListItem[]; count: number }>("/api/v1/stocks");
      return data;
    },
  });
}

export function useStockDetail(ticker: string) {
  return useQuery({
    queryKey: ["stock", ticker],
    queryFn: async () => {
      const { data } = await apiClient.get<StockDetail>(`/api/v1/stocks/${ticker}`);
      return data;
    },
    enabled: !!ticker,
  });
}

export function useStockHistory(ticker: string, page = 1, pageSize = 100) {
  return useQuery({
    queryKey: ["stockHistory", ticker, page, pageSize],
    queryFn: async () => {
      const { data } = await apiClient.get<{ ticker: string; data: StockHistoryItem[]; count: number }>(
        `/api/v1/stocks/${ticker}/history?page=${page}&page_size=${pageSize}`
      );
      return data;
    },
    enabled: !!ticker,
  });
}
