"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Typography, Divider,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import PieChartIcon from "@mui/icons-material/PieChart";
import SettingsIcon from "@mui/icons-material/Settings";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  width: number;
  isMobile: boolean;
}

const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Predictions", path: "/predictions", icon: <TrendingUpIcon /> },
  { label: "Portfolio", path: "/portfolio", icon: <PieChartIcon /> },
  { label: "Pipeline", path: "/pipeline", icon: <SettingsIcon /> },
];

export default function Sidebar({ open, onClose, width, isMobile }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const handleNavigate = (path: string) => {
    router.push(path);
    if (isMobile) onClose();
  };

  const drawerContent = (
    <Box sx={{ pt: 2, pb: 2 }}>
      <Box sx={{ px: 3, mb: 3, display: "flex", alignItems: "center", gap: 1 }}>
        <TrendingUpIcon sx={{ color: "primary.main", fontSize: 28 }} />
        <Typography variant="h5" sx={{ color: "primary.main", fontWeight: 700 }}>
          FinSense
        </Typography>
      </Box>
      <Divider sx={{ borderColor: "rgba(255,255,255,0.06)", mb: 1 }} />
      <List sx={{ px: 1 }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path;
          return (
            <ListItemButton
              key={item.path}
              onClick={() => handleNavigate(item.path)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                bgcolor: isActive ? "rgba(0,212,170,0.12)" : "transparent",
                "&:hover": { bgcolor: "rgba(0,212,170,0.08)" },
              }}
            >
              <ListItemIcon
                sx={{ color: isActive ? "primary.main" : "text.secondary", minWidth: 40 }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                sx={{ "& .MuiTypography-root": { color: isActive ? "primary.main" : "text.primary", fontWeight: isActive ? 600 : 400 } }}
              />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Drawer
      variant={isMobile ? "temporary" : "persistent"}
      open={open}
      onClose={onClose}
      sx={{
        width: open ? width : 0,
        flexShrink: 0,
        "& .MuiDrawer-paper": { width, boxSizing: "border-box" },
      }}
    >
      {drawerContent}
    </Drawer>
  );
}
