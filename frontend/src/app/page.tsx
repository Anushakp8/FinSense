"use client";

import { Typography, Box } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";

export default function DashboardPage() {
  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <DashboardIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Dashboard</Typography>
      </Box>
      <Typography variant="body1" color="text.secondary">
        Welcome to FinSense. Data integration coming in Phase 8.
      </Typography>
    </Box>
  );
}
