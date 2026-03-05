"use client";

import { Typography, Box } from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";

export default function PredictionsPage() {
  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <TrendingUpIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Predictions</Typography>
      </Box>
      <Typography variant="body1" color="text.secondary">
        ML predictions interface coming in Phase 8.
      </Typography>
    </Box>
  );
}
