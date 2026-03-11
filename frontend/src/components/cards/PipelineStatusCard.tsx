import { Card, CardContent, Typography, Box, Chip } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";

interface PipelineStatusCardProps {
  status: "healthy" | "degraded" | "failed";
  message: string;
  freshness: number | null;
}

const statusConfig = {
  healthy: { icon: <CheckCircleIcon />, color: "#00C48C", label: "Healthy" },
  degraded: { icon: <WarningIcon />, color: "#FFB020", label: "Degraded" },
  failed: { icon: <ErrorIcon />, color: "#FF6B6B", label: "Failed" },
};

export default function PipelineStatusCard({ status, message, freshness }: PipelineStatusCardProps) {
  const config = statusConfig[status];
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
          <Typography variant="body2" color="text.secondary">Pipeline Status</Typography>
          <Chip
            size="small"
            icon={config.icon}
            label={config.label}
            sx={{ bgcolor: `${config.color}20`, color: config.color, fontWeight: 600 }}
          />
        </Box>
        <Typography variant="body1" sx={{ mt: 1 }}>{message}</Typography>
        {freshness !== null && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Data freshness: {freshness.toFixed(1)}h ago
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
