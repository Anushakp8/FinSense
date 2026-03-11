import { Card, CardContent, Typography, Box, Chip } from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";

interface StockCardProps {
  ticker: string;
  price: number;
  changePct: number;
  volume: number;
  onClick?: () => void;
}

export default function StockCard({ ticker, price, changePct, volume, onClick }: StockCardProps) {
  const isUp = changePct >= 0;
  return (
    <Card
      onClick={onClick}
      sx={{ cursor: onClick ? "pointer" : "default", "&:hover": onClick ? { borderColor: "primary.main" } : {} }}
    >
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
          <Typography variant="h6" fontWeight={700}>{ticker}</Typography>
          <Chip
            size="small"
            icon={isUp ? <TrendingUpIcon /> : <TrendingDownIcon />}
            label={`${isUp ? "+" : ""}${changePct.toFixed(2)}%`}
            sx={{
              bgcolor: isUp ? "rgba(0,196,140,0.15)" : "rgba(255,107,107,0.15)",
              color: isUp ? "success.main" : "error.main",
              fontWeight: 600,
            }}
          />
        </Box>
        <Typography variant="h4" fontWeight={700}>${price.toFixed(2)}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Vol: {(volume / 1_000_000).toFixed(1)}M
        </Typography>
      </CardContent>
    </Card>
  );
}
