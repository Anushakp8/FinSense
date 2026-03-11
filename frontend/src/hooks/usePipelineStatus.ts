import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import type { PipelineStatus } from "@/types";

export function usePipelineStatus() {
  return useQuery({
    queryKey: ["pipelineStatus"],
    queryFn: async () => {
      const { data } = await apiClient.get<PipelineStatus>("/api/v1/pipeline-status");
      return data;
    },
    refetchInterval: 60000,
  });
}
