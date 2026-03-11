import { Card, CardContent, Typography, Box } from "@mui/material";
import SmartToyIcon from "@mui/icons-material/SmartToy";

interface ModelPerformanceCardProps {
  modelName: string | null;
  version: string | null;
  f1: number | null;
}

export default function ModelPerformanceCard({ modelName, version, f1 }: ModelPerformanceCardProps) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <SmartToyIcon sx={{ color: "primary.main", fontSize: 20 }} />
          <Typography variant="body2" color="text.secondary">Active Model</Typography>
        </Box>
        {modelName ? (
          <>
            <Typography variant="h6" fontWeight={600}>{modelName}</Typography>
            <Typography variant="body2" color="text.secondary">v{version}</Typography>
            {f1 !== null && (
              <Typography variant="body2" sx={{ mt: 0.5, color: "primary.main" }}>
                F1 Score: {(f1 * 100).toFixed(1)}%
              </Typography>
            )}
          </>
        ) : (
          <Typography variant="body2" color="text.secondary">No active model</Typography>
        )}
      </CardContent>
    </Card>
  );
}
