import { Card, CardContent, Skeleton, Box } from "@mui/material";

export default function ChartSkeleton() {
  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="30%" height={28} />
        <Box sx={{ mt: 2 }}>
          <Skeleton variant="rectangular" width="100%" height={300} sx={{ borderRadius: 2 }} />
        </Box>
      </CardContent>
    </Card>
  );
}
