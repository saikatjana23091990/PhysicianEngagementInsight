import React from "react";
import { Card, CardContent, Typography, Box, Stack, Chip } from "@mui/material";
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import TrendingDownRoundedIcon from "@mui/icons-material/TrendingDownRounded";
import { palette } from "../theme/kiwiTheme";

export default function KPICard({ label, value, unit, sublabel, delta, trend = "up", accent = palette.primary, testid }) {
  const positive = trend === "up";
  return (
    <Card data-testid={testid} className="fade-up" sx={{ height: "100%", overflow: "hidden", position: "relative" }}>
      <Box
        sx={{
          position: "absolute",
          right: -34,
          top: -34,
          width: 120,
          height: 120,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${accent}40 0%, transparent 70%)`,
          filter: "blur(2px)",
        }}
      />
      <CardContent sx={{ position: "relative" }}>
        <Typography variant="overline" sx={{ color: palette.textMuted }}>
          {label}
        </Typography>
        <Stack direction="row" alignItems="baseline" spacing={0.8} sx={{ mt: 0.5 }}>
          <Typography variant="h3" sx={{ fontFamily: "Sora", color: accent, lineHeight: 1 }}>
            {value}
          </Typography>
          {unit && (
            <Typography variant="h6" sx={{ color: palette.textMuted }}>
              {unit}
            </Typography>
          )}
        </Stack>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mt: 1.5 }}>
          {delta !== undefined && delta !== null && (
            <Chip
              size="small"
              icon={positive ? <TrendingUpRoundedIcon /> : <TrendingDownRoundedIcon />}
              label={`${positive ? "+" : ""}${delta}`}
              sx={{
                bgcolor: positive ? "rgba(10,182,139,0.14)" : "rgba(208,74,74,0.12)",
                color: positive ? palette.primary : palette.danger,
                "& .MuiChip-icon": { color: positive ? palette.primary : palette.danger },
                fontWeight: 700,
              }}
            />
          )}
          {sublabel && (
            <Typography variant="caption" sx={{ color: palette.textMuted }}>
              {sublabel}
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
