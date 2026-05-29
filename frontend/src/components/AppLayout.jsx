import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Box, Drawer, Toolbar, AppBar, Typography, List, ListItemButton,
  ListItemIcon, ListItemText, Avatar, Chip, IconButton, Tooltip, Menu, MenuItem,
  Stack, Divider,
} from "@mui/material";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import GroupsRoundedIcon from "@mui/icons-material/GroupsRounded";
import PersonSearchRoundedIcon from "@mui/icons-material/PersonSearchRounded";
import EventNoteRoundedIcon from "@mui/icons-material/EventNoteRounded";
import MapRoundedIcon from "@mui/icons-material/MapRounded";
import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import HubRoundedIcon from "@mui/icons-material/HubRounded";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import ChatRoundedIcon from "@mui/icons-material/ChatRounded";
import SettingsRoundedIcon from "@mui/icons-material/SettingsRounded";
import SwapHorizRoundedIcon from "@mui/icons-material/SwapHorizRounded";
import { palette } from "../theme/kiwiTheme";

const DRAWER_W = 248;

const NAV = [
  { to: "/executive", label: "Executive", icon: <DashboardRoundedIcon fontSize="small" />, roles: ["Executive", "Manager"] },
  { to: "/rep", label: "Rep Home", icon: <GroupsRoundedIcon fontSize="small" />, roles: ["Rep", "Manager"] },
  { to: "/hcp", label: "HCPs", icon: <PersonSearchRoundedIcon fontSize="small" />, roles: ["Rep", "Manager", "Executive"] },
  { to: "/briefing", label: "Pre-Call Brief", icon: <EventNoteRoundedIcon fontSize="small" />, roles: ["Rep", "Manager"] },
  { to: "/nba", label: "Next Best Action", icon: <BoltRoundedIcon fontSize="small" />, roles: ["Rep", "Manager"] },
  { to: "/conversion", label: "Conversion", icon: <TrendingUpRoundedIcon fontSize="small" />, roles: ["Manager", "Executive"] },
  { to: "/territory", label: "Territory", icon: <MapRoundedIcon fontSize="small" />, roles: ["Manager", "Executive"] },
  { to: "/manager/daily-plan", label: "Team Plans", icon: <GroupsRoundedIcon fontSize="small" />, roles: ["Manager", "Executive"] },
  { to: "/kol", label: "KOL Analytics", icon: <HubRoundedIcon fontSize="small" />, roles: ["Manager", "Executive"] },
  { to: "/chat", label: "Ask Data", icon: <ChatRoundedIcon fontSize="small" />, roles: ["Rep", "Manager", "Executive"] },
  { to: "/sources", label: "Source Explorer", icon: <StorageRoundedIcon fontSize="small" />, roles: ["Manager", "Executive"] },
  // { to: "/settings", label: "Settings", icon: <SettingsRoundedIcon fontSize="small" />, roles: ["Executive"] },
];

const ROLES = ["Executive", "Manager", "Rep"];

export default function AppLayout({ children }) {
  const location = useLocation();
  const [role, setRole] = useState(() => localStorage.getItem("ca_role") || "Executive");
  const [anchor, setAnchor] = useState(null);

  const setRoleAndSave = (r) => {
    setRole(r);
    localStorage.setItem("ca_role", r);
    setAnchor(null);
  };

  const filteredNav = NAV.filter((n) => n.roles.includes(role));

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          ml: `${DRAWER_W}px`,
          width: `calc(100% - ${DRAWER_W}px)`,
          background: "rgba(255,255,255,0.85)",
          backdropFilter: "blur(12px)",
          borderBottom: `1px solid ${palette.border}`,
          color: palette.text,
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Box>
            <Typography variant="overline" sx={{ color: palette.textMuted }}>
              Physician Engagement Insight Platform
            </Typography>
            <Typography variant="h6" sx={{ lineHeight: 1.1 }}>
              {currentTitle(location.pathname)}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Chip
              size="small"
              label="Powered by AWS Bedrock"
              sx={{
                bgcolor: "rgba(2,129,116,0.08)",
                color: palette.primary,
                border: `1px solid ${palette.border}`,
                fontWeight: 600,
              }}
              data-testid="provider-chip"
            />
            <Tooltip title="Switch role">
              <Chip
                onClick={(e) => setAnchor(e.currentTarget)}
                icon={<SwapHorizRoundedIcon />}
                label={`Role: ${role}`}
                clickable
                data-testid="role-switcher"
                sx={{
                  bgcolor: palette.cream,
                  color: palette.primaryDark,
                  fontWeight: 700,
                  border: "none",
                  "& .MuiChip-icon": { color: palette.primaryDark },
                }}
              />
            </Tooltip>
            <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
              {ROLES.map((r) => (
                <MenuItem key={r} onClick={() => setRoleAndSave(r)} selected={r === role} data-testid={`role-option-${r.toLowerCase()}`}>
                  {r}
                </MenuItem>
              ))}
            </Menu>
            <Avatar sx={{ bgcolor: palette.primary, fontFamily: "Sora", fontWeight: 700 }}>
              {role[0]}
            </Avatar>
          </Stack>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_W,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: DRAWER_W,
            borderRight: `1px solid ${palette.border}`,
            background: "linear-gradient(180deg, #FFFFFF 0%, #F4F9F4 100%)",
            boxSizing: "border-box",
          },
        }}
      >
        <Box sx={{ p: 2.5, display: "flex", alignItems: "center", gap: 1.5 }}>
          <Box
            sx={{
              width: 38,
              height: 38,
              borderRadius: "12px",
              background: `linear-gradient(135deg, ${palette.primary} 0%, ${palette.accent} 100%)`,
              display: "grid",
              placeItems: "center",
              color: "#fff",
              fontFamily: "Sora",
              fontWeight: 800,
              fontSize: 18,
              boxShadow: "0 6px 18px -6px rgba(2,129,116,0.45)",
            }}
          >
            VI
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontFamily: "Sora", fontWeight: 800, lineHeight: 1, fontSize: 17 }}>
              Vyntrix Intelligence<span style={{ color: palette.accent }}>.</span>
            </Typography>
            <Typography variant="caption" sx={{ color: palette.textMuted }}>
              Physician Insight
            </Typography>
          </Box>
        </Box>
        <Divider />
        <List sx={{ px: 1.5, py: 1 }}>
          {filteredNav.map((item) => {
            const active =
              location.pathname === item.to ||
              (item.to !== "/" && location.pathname.startsWith(item.to));
            return (
              <ListItemButton
                key={item.to}
                component={Link}
                to={item.to}
                selected={active}
                data-testid={`nav-${item.to.replace("/", "")}`}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  px: 1.5,
                  py: 1.1,
                  color: active ? palette.primaryDark : palette.text,
                  "&.Mui-selected": {
                    background: "rgba(10, 182, 139, 0.12)",
                    color: palette.primaryDark,
                    fontWeight: 700,
                    "&:hover": { background: "rgba(10, 182, 139, 0.18)" },
                  },
                  "& .MuiListItemIcon-root": {
                    color: active ? palette.primary : palette.textMuted,
                    minWidth: 34,
                  },
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ fontSize: 14, fontWeight: active ? 700 : 500 }}
                />
              </ListItemButton>
            );
          })}
        </List>
        {/* <Box sx={{ mt: "auto", p: 2 }}>
          <Box
            sx={{
              borderRadius: 3,
              p: 1.75,
              background: `linear-gradient(135deg, ${palette.primary} 0%, ${palette.accent} 100%)`,
              color: "#fff",
            }}
          >
            <Typography variant="overline" sx={{ opacity: 0.8 }}>
              Demo build
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Synthetic data · Source-only
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.85 }}>
              All metrics computed at runtime.
            </Typography>
          </Box>
        </Box> */}
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 4,
          pt: 11,
          width: `calc(100% - ${DRAWER_W}px)`,
          minHeight: "100vh",
        }}
      >
        {children}
      </Box>
    </Box>
  );
}

function currentTitle(pathname) {
  const item = NAV.find((n) => pathname.startsWith(n.to)) || { label: "Overview" };
  return item.label;
}
