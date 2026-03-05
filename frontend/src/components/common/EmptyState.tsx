import { Box, Typography } from "@mui/material";
import InboxIcon from "@mui/icons-material/Inbox";

interface EmptyStateProps {
  message?: string;
  icon?: React.ReactNode;
}

export default function EmptyState({
  message = "No data available",
  icon,
}: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        py: 8,
        color: "text.secondary",
      }}
    >
      {icon || <InboxIcon sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />}
      <Typography variant="body1">{message}</Typography>
    </Box>
  );
}
