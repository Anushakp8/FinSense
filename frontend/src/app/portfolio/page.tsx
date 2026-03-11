"use client";

import { useState } from "react";
import { Typography, Box, Card, CardContent, Grid, TextField, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from "@mui/material";
import PieChartIcon from "@mui/icons-material/PieChart";
import { usePortfolioRisk } from "@/hooks/usePortfolioRisk";
import ErrorState from "@/components/common/ErrorState";
import CardSkeleton from "@/components/skeletons/CardSkeleton";

export default function PortfolioPage() {
  const [tickerInput, setTickerInput] = useState("AAPL,MSFT,GOOGL");
  const [weightInput, setWeightInput] = useState("0.4,0.3,0.3");
  const [tickers, setTickers] = useState<string[]>([]);
  const [weights, setWeights] = useState<number[]>([]);

  const risk = usePortfolioRisk(tickers, weights);

  const handleAnalyze = () => {
    const t = tickerInput.split(",").map((s) => s.trim().toUpperCase());
    const w = weightInput.split(",").map((s) => parseFloat(s.trim()));
    setTickers(t);
    setWeights(w);
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <PieChartIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Portfolio Risk</Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Portfolio Builder</Typography>
              <TextField
                fullWidth label="Tickers (comma-separated)" value={tickerInput}
                onChange={(e) => setTickerInput(e.target.value)}
                sx={{ mb: 2 }} placeholder="AAPL,MSFT,GOOGL"
              />
              <TextField
                fullWidth label="Weights (must sum to 1.0)" value={weightInput}
                onChange={(e) => setWeightInput(e.target.value)}
                sx={{ mb: 2 }} placeholder="0.4,0.3,0.3"
              />
              <Button variant="contained" fullWidth onClick={handleAnalyze} sx={{ py: 1.5 }}>
                Analyze Risk
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 7 }}>
          {risk.isLoading && <CardSkeleton />}
          {risk.isError && <ErrorState message={risk.error?.message || "Analysis failed"} />}
          {risk.data && (
            <>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                {[
                  { label: "VaR (95%)", value: `${(risk.data.var_95 * 100).toFixed(2)}%`, color: "#FF6B6B" },
                  { label: "VaR (99%)", value: `${(risk.data.var_99 * 100).toFixed(2)}%`, color: "#FFB020" },
                  { label: "Expected Return", value: `${(risk.data.expected_return * 100).toFixed(1)}%`, color: "#00C48C" },
                  { label: "Max Drawdown", value: `${(risk.data.max_drawdown * 100).toFixed(1)}%`, color: "#FF6B6B" },
                ].map((m) => (
                  <Grid size={{ xs: 6, sm: 3 }} key={m.label}>
                    <Card>
                      <CardContent sx={{ textAlign: "center", py: 2 }}>
                        <Typography variant="body2" color="text.secondary">{m.label}</Typography>
                        <Typography variant="h5" fontWeight={700} sx={{ color: m.color }}>{m.value}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Individual Stock Risk</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ color: "text.secondary" }}>Ticker</TableCell>
                          <TableCell align="right" sx={{ color: "text.secondary" }}>Weight</TableCell>
                          <TableCell align="right" sx={{ color: "text.secondary" }}>Ann. Volatility</TableCell>
                          <TableCell align="right" sx={{ color: "text.secondary" }}>VaR (95%)</TableCell>
                          <TableCell align="right" sx={{ color: "text.secondary" }}>Exp. Return</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {risk.data.individual_risks.map((r) => (
                          <TableRow key={r.ticker}>
                            <TableCell sx={{ fontWeight: 600 }}>{r.ticker}</TableCell>
                            <TableCell align="right">{(r.weight * 100).toFixed(0)}%</TableCell>
                            <TableCell align="right">{(r.annual_volatility * 100).toFixed(1)}%</TableCell>
                            <TableCell align="right" sx={{ color: "error.main" }}>
                              {(r.var_95 * 100).toFixed(2)}%
                            </TableCell>
                            <TableCell align="right" sx={{ color: r.expected_return >= 0 ? "success.main" : "error.main" }}>
                              {(r.expected_return * 100).toFixed(1)}%
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
