"use client";

import { useState } from "react";
import { Typography, Box, Grid, Card, CardContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import { useStocks, useStockHistory } from "@/hooks/useStocks";
import { usePipelineStatus } from "@/hooks/usePipelineStatus";
import StockChart from "@/components/charts/StockChart";
import PipelineStatusCard from "@/components/cards/PipelineStatusCard";
import ModelPerformanceCard from "@/components/cards/ModelPerformanceCard";
import CardSkeleton from "@/components/skeletons/CardSkeleton";
import ChartSkeleton from "@/components/skeletons/ChartSkeleton";
import TableSkeleton from "@/components/skeletons/TableSkeleton";
import ErrorState from "@/components/common/ErrorState";

export default function DashboardPage() {
  const [selectedTicker, setSelectedTicker] = useState("AAPL");
  const stocks = useStocks();
  const history = useStockHistory(selectedTicker, 1, 100);
  const pipeline = usePipelineStatus();

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <DashboardIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Dashboard</Typography>
      </Box>

      {/* Top metric cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {stocks.isLoading ? <CardSkeleton /> : stocks.isError ? (
            <ErrorState message="Failed to load stocks" onRetry={() => stocks.refetch()} />
          ) : (
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary">Stocks Tracked</Typography>
                <Typography variant="h3" fontWeight={700} sx={{ color: "primary.main" }}>
                  {stocks.data?.count ?? 0}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {pipeline.isLoading ? <CardSkeleton /> : (
            <PipelineStatusCard
              status={pipeline.data?.status ?? "failed"}
              message={pipeline.data?.message ?? "Unknown"}
              freshness={pipeline.data?.data_freshness_hours ?? null}
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {pipeline.isLoading ? <CardSkeleton /> : (
            <ModelPerformanceCard
              modelName={(pipeline.data?.active_model as Record<string, string> | null)?.model_name ?? null}
              version={(pipeline.data?.active_model as Record<string, string> | null)?.version ?? null}
              f1={pipeline.data?.active_model ? Number((pipeline.data.active_model as Record<string, number>).f1) : null}
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Data Points</Typography>
              <Typography variant="h3" fontWeight={700} sx={{ color: "primary.main" }}>
                {pipeline.data?.row_counts?.raw_prices ? (pipeline.data.row_counts.raw_prices / 1000).toFixed(0) + "K" : "..."}
              </Typography>
              <Typography variant="body2" color="text.secondary">raw price records</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Stock chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          {history.isLoading ? <ChartSkeleton /> : history.isError ? (
            <ErrorState message="Failed to load chart data" onRetry={() => history.refetch()} />
          ) : history.data?.data ? (
            <StockChart data={history.data.data} ticker={selectedTicker} />
          ) : null}
        </CardContent>
      </Card>

      {/* Stocks table */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>All Tracked Stocks</Typography>
          {stocks.isLoading ? <TableSkeleton /> : stocks.isError ? (
            <ErrorState message="Failed to load stocks" onRetry={() => stocks.refetch()} />
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ color: "text.secondary", fontWeight: 600 }}>Ticker</TableCell>
                    <TableCell align="right" sx={{ color: "text.secondary", fontWeight: 600 }}>Price</TableCell>
                    <TableCell align="right" sx={{ color: "text.secondary", fontWeight: 600 }}>Change</TableCell>
                    <TableCell align="right" sx={{ color: "text.secondary", fontWeight: 600 }}>Volume</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {stocks.data?.stocks.map((stock) => {
                    const isUp = stock.change_pct >= 0;
                    return (
                      <TableRow
                        key={stock.ticker}
                        hover
                        onClick={() => setSelectedTicker(stock.ticker)}
                        sx={{ cursor: "pointer", bgcolor: stock.ticker === selectedTicker ? "rgba(0,212,170,0.06)" : "transparent" }}
                      >
                        <TableCell sx={{ fontWeight: 600 }}>{stock.ticker}</TableCell>
                        <TableCell align="right">${stock.latest_price.toFixed(2)}</TableCell>
                        <TableCell align="right">
                          <Chip
                            size="small"
                            icon={isUp ? <TrendingUpIcon sx={{ fontSize: 14 }} /> : <TrendingDownIcon sx={{ fontSize: 14 }} />}
                            label={`${isUp ? "+" : ""}${stock.change_pct.toFixed(2)}%`}
                            sx={{
                              bgcolor: isUp ? "rgba(0,196,140,0.15)" : "rgba(255,107,107,0.15)",
                              color: isUp ? "success.main" : "error.main",
                              fontWeight: 600, fontSize: 12,
                            }}
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ color: "text.secondary" }}>
                          {(stock.volume / 1_000_000).toFixed(1)}M
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
