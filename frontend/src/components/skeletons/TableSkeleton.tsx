import { Card, CardContent, Skeleton, Box } from "@mui/material";

export default function TableSkeleton() {
  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="25%" height={28} sx={{ mb: 2 }} />
        {Array.from({ length: 5 }).map((_, i) => (
          <Box key={i} sx={{ display: "flex", gap: 2, mb: 1.5 }}>
            <Skeleton variant="text" width="15%" height={20} />
            <Skeleton variant="text" width="20%" height={20} />
            <Skeleton variant="text" width="15%" height={20} />
            <Skeleton variant="text" width="25%" height={20} />
            <Skeleton variant="text" width="15%" height={20} />
          </Box>
        ))}
      </CardContent>
    </Card>
  );
}
