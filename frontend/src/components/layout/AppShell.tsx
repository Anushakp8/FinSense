"use client";

import { useState } from "react";
import { Box, useMediaQuery, useTheme } from "@mui/material";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

const DRAWER_WIDTH = 260;

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  const handleToggleSidebar = () => setSidebarOpen((prev) => !prev);

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "background.default" }}>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        width={DRAWER_WIDTH}
        isMobile={isMobile}
      />
      <Box
        sx={{
          flexGrow: 1,
          ml: isMobile ? 0 : sidebarOpen ? `${DRAWER_WIDTH}px` : 0,
          transition: "margin-left 0.3s ease",
        }}
      >
        <TopBar onMenuClick={handleToggleSidebar} />
        <Box
          component="main"
          sx={{
            p: { xs: 2, sm: 3 },
            mt: "64px",
            maxWidth: 1400,
            mx: "auto",
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
}
