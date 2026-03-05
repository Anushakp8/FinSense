import { Alert, AlertTitle, Button, Box } from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message = "Something went wrong. Please try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <Box sx={{ p: 2 }}>
      <Alert
        severity="error"
        sx={{
          bgcolor: "rgba(255,107,107,0.1)",
          border: "1px solid rgba(255,107,107,0.3)",
          "& .MuiAlert-icon": { color: "#FF6B6B" },
        }}
        action={
          onRetry ? (
            <Button
              color="inherit"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={onRetry}
            >
              Retry
            </Button>
          ) : undefined
        }
      >
        <AlertTitle>Error</AlertTitle>
        {message}
      </Alert>
    </Box>
  );
}
