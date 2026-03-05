"use client";

import { Typography, Box } from "@mui/material";
import PieChartIcon from "@mui/icons-material/PieChart";

export default function PortfolioPage() {
  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <PieChartIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Portfolio Risk</Typography>
      </Box>
      <Typography variant="body1" color="text.secondary">
        Portfolio risk analysis coming in Phase 8.
      </Typography>
    </Box>
  );
}
