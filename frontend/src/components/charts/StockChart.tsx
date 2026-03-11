"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Box, Typography } from "@mui/material";
import type { StockHistoryItem } from "@/types";

interface StockChartProps {
  data: StockHistoryItem[];
  ticker: string;
}

export default function StockChart({ data, ticker }: StockChartProps) {
  const chartData = [...data].reverse().map((d) => ({
    date: new Date(d.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    close: d.close,
    high: d.high,
    low: d.low,
  }));

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>{ticker} Price History</Typography>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00D4AA" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" stroke="#94A3B8" fontSize={12} tickLine={false} />
          <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#111D33",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color: "#F8FAFC",
            }}
          />
          <Area type="monotone" dataKey="close" stroke="#00D4AA" fill="url(#colorClose)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </Box>
  );
}
