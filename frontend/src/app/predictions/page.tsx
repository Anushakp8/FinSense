"use client";

import { useState } from "react";
import { Typography, Box, Card, CardContent, Grid, Select, MenuItem, Button, LinearProgress } from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import { useStocks } from "@/hooks/useStocks";
import { usePrediction } from "@/hooks/usePredictions";
import CardSkeleton from "@/components/skeletons/CardSkeleton";
import ErrorState from "@/components/common/ErrorState";

export default function PredictionsPage() {
  const [selectedTicker, setSelectedTicker] = useState("AAPL");
  const stocks = useStocks();
  const prediction = usePrediction();

  const handlePredict = () => {
    prediction.mutate(selectedTicker);
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <TrendingUpIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Predictions</Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Request Prediction</Typography>
              {stocks.isLoading ? <CardSkeleton /> : (
                <>
                  <Select
                    value={selectedTicker}
                    onChange={(e) => setSelectedTicker(e.target.value)}
                    fullWidth
                    sx={{ mb: 2, bgcolor: "background.default" }}
                  >
                    {stocks.data?.stocks.map((s) => (
                      <MenuItem key={s.ticker} value={s.ticker}>
                        {s.ticker} - ${s.latest_price.toFixed(2)}
                      </MenuItem>
                    ))}
                  </Select>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handlePredict}
                    disabled={prediction.isPending}
                    sx={{ py: 1.5, fontSize: 16 }}
                  >
                    {prediction.isPending ? "Predicting..." : `Predict ${selectedTicker}`}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ minHeight: 200 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Prediction Result</Typography>
              {prediction.isPending && <LinearProgress sx={{ mb: 2 }} />}
              {prediction.isError && (
                <ErrorState message={prediction.error?.message || "Prediction failed"} onRetry={handlePredict} />
              )}
              {prediction.data && (
                <Box sx={{ textAlign: "center", py: 2 }}>
                  <Box sx={{
                    display: "inline-flex", alignItems: "center", justifyContent: "center",
                    width: 80, height: 80, borderRadius: "50%", mb: 2,
                    bgcolor: prediction.data.direction === "UP" ? "rgba(0,196,140,0.15)" : "rgba(255,107,107,0.15)",
                  }}>
                    {prediction.data.direction === "UP"
                      ? <ArrowUpwardIcon sx={{ fontSize: 40, color: "success.main" }} />
                      : <ArrowDownwardIcon sx={{ fontSize: 40, color: "error.main" }} />}
                  </Box>
                  <Typography variant="h4" fontWeight={700}
                    sx={{ color: prediction.data.direction === "UP" ? "success.main" : "error.main" }}
                  >
                    {prediction.data.direction}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
                    Confidence: {(prediction.data.confidence * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Model: {prediction.data.model_name} v{prediction.data.model_version}
                  </Typography>
                </Box>
              )}
              {!prediction.data && !prediction.isPending && !prediction.isError && (
                <Typography variant="body1" color="text.secondary" sx={{ textAlign: "center", py: 4 }}>
                  Select a ticker and click Predict
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
