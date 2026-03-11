import { useMutation } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import type { PredictionResponse } from "@/types";

export function usePrediction() {
  return useMutation({
    mutationFn: async (ticker: string) => {
      const { data } = await apiClient.post<PredictionResponse>("/api/v1/predict", { ticker });
      return data;
    },
  });
}
