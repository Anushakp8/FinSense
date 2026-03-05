"use client";

import { Typography, Box } from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";

export default function PipelinePage() {
  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <SettingsIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Pipeline Status</Typography>
      </Box>
      <Typography variant="body1" color="text.secondary">
        Pipeline monitoring coming in Phase 8.
      </Typography>
    </Box>
  );
}
