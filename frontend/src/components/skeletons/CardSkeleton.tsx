import { Card, CardContent, Skeleton, Box } from "@mui/material";

export default function CardSkeleton() {
  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="40%" height={24} />
        <Skeleton variant="text" width="60%" height={40} sx={{ mt: 1 }} />
        <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
          <Skeleton variant="rounded" width={60} height={24} />
          <Skeleton variant="rounded" width={80} height={24} />
        </Box>
      </CardContent>
    </Card>
  );
}
