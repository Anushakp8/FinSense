"use client";

import { createTheme } from "@mui/material/styles";

const finsenseMidnight = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#00D4AA", light: "#33DDBB", dark: "#00A888" },
    secondary: { main: "#0A1628" },
    background: { default: "#0A1628", paper: "#111D33" },
    error: { main: "#FF6B6B" },
    warning: { main: "#FFB020" },
    success: { main: "#00C48C" },
    text: { primary: "#F8FAFC", secondary: "#94A3B8" },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontSize: "2.25rem", fontWeight: 700, letterSpacing: "-0.02em" },
    h2: { fontSize: "1.75rem", fontWeight: 600, letterSpacing: "-0.01em" },
    h3: { fontSize: "1.5rem", fontWeight: 600 },
    h4: { fontSize: "1.25rem", fontWeight: 600 },
    h5: { fontSize: "1rem", fontWeight: 600 },
    h6: { fontSize: "0.875rem", fontWeight: 600 },
    body1: { fontSize: "0.9375rem", lineHeight: 1.6 },
    body2: { fontSize: "0.8125rem", lineHeight: 1.5 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          backgroundColor: "#111D33",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 16,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600, borderRadius: 10 },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          backgroundColor: "#0D1B2A",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: "#0D1B2A",
          borderRight: "1px solid rgba(255,255,255,0.06)",
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: { backgroundColor: "rgba(255,255,255,0.05)" },
      },
    },
  },
});

export default finsenseMidnight;
