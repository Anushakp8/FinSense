"use client";

import { Typography, Box, Card, CardContent, Grid, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import { usePipelineStatus } from "@/hooks/usePipelineStatus";
import CardSkeleton from "@/components/skeletons/CardSkeleton";
import ErrorState from "@/components/common/ErrorState";

const statusIcons = {
  healthy: <CheckCircleIcon sx={{ color: "#00C48C" }} />,
  degraded: <WarningIcon sx={{ color: "#FFB020" }} />,
  failed: <ErrorIcon sx={{ color: "#FF6B6B" }} />,
};

const statusColors = { healthy: "#00C48C", degraded: "#FFB020", failed: "#FF6B6B" };

export default function PipelinePage() {
  const pipeline = usePipelineStatus();

  if (pipeline.isLoading) return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Pipeline Status</Typography>
      <Grid container spacing={2}>
        {[1, 2, 3, 4].map((i) => <Grid size={{ xs: 12, sm: 6 }} key={i}><CardSkeleton /></Grid>)}
      </Grid>
    </Box>
  );

  if (pipeline.isError) return <ErrorState message="Failed to load pipeline status" onRetry={() => pipeline.refetch()} />;

  const data = pipeline.data;
  if (!data) return null;

  const model = data.active_model as Record<string, string | number> | null;

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
        <SettingsIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h4">Pipeline Status</Typography>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              {statusIcons[data.status]}
              <Typography variant="h5" fontWeight={700} sx={{ color: statusColors[data.status], mt: 1 }}>
                {data.status.toUpperCase()}
              </Typography>
              <Typography variant="body2" color="text.secondary">{data.message}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">Data Freshness</Typography>
              <Typography variant="h5" fontWeight={700} sx={{ color: "primary.main" }}>
                {data.data_freshness_hours ? `${data.data_freshness_hours.toFixed(1)}h` : "N/A"}
              </Typography>
              <Typography variant="body2" color="text.secondary">since last update</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">Active Model</Typography>
              <Typography variant="h6" fontWeight={600}>
                {model ? String(model.model_name) : "None"}
              </Typography>
              {model && <Chip size="small" label={`v${model.version}`} sx={{ mt: 0.5, bgcolor: "rgba(0,212,170,0.15)", color: "primary.main" }} />}
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">Model F1 Score</Typography>
              <Typography variant="h5" fontWeight={700} sx={{ color: "primary.main" }}>
                {model ? `${(Number(model.f1) * 100).toFixed(1)}%` : "N/A"}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Row Counts</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: "text.secondary" }}>Table</TableCell>
                  <TableCell align="right" sx={{ color: "text.secondary" }}>Rows</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(data.row_counts).map(([table, count]) => (
                  <TableRow key={table}>
                    <TableCell sx={{ fontWeight: 500 }}>{table}</TableCell>
                    <TableCell align="right">{Number(count).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
