"use client";

import { ThemeProvider, CssBaseline } from "@mui/material";
import { QueryClientProvider } from "@tanstack/react-query";
import finsenseMidnight from "@/theme/finsenseMidnight";
import queryClient from "@/lib/queryClient";
import AppShell from "@/components/layout/AppShell";

export default function ThemeRegistry({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={finsenseMidnight}>
        <CssBaseline />
        <AppShell>{children}</AppShell>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
