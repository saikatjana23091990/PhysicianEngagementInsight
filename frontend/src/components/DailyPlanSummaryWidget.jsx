import React from "react";
import {
  Box,
  Card,
  CardContent,
  Stack,
  Typography,
  Chip,
  Button,
  CircularProgress,
} from "@mui/material";
import { palette } from "../theme/kiwiTheme";

const metricCardStyle = (accentColor, bgColor) => ({
  p: 2.5,
  borderRadius: "20px",
  bgcolor: bgColor,
  border: `1px solid ${palette.border}`,
  boxShadow: "0px 4px 18px rgba(43,35,56,0.04)",
  minHeight: 140,
  display: "flex",
  flexDirection: "column",
  justifyContent: "space-between",
  position: "relative",
  overflow: "hidden",
  transition: "all 0.2s ease",

  "&:hover": {
    transform: "translateY(-2px)",
    boxShadow: "0px 8px 24px rgba(43,35,56,0.08)",
  },

  "&::after": {
    content: '""',
    position: "absolute",
    left: 20,
    right: 20,
    bottom: 12,
    height: 4,
    borderRadius: 4,
    backgroundColor: accentColor,
  },
});

export default function DailyPlanSummaryWidget({
  plan,
  onReplan,
  loading,
}) {
  const summary = plan?.summary || {};

  const metrics = [
    {
      label: "Planned Actions",
      value: summary.total_planned_actions ?? 0,
      color: palette.primary,
      bg: `${palette.primary}10`,
    },
    {
      label: "Expected Conversions",
      value: summary.expected_conversions ?? 0,
      color: palette.accent,
      bg: `${palette.accent}10`,
    },
    {
      label: "High Priority",
      value: summary.high_priority_activities ?? 0,
      color: palette.light,
      bg: `${palette.light}10`,
    },
    {
      label: "KOL Engagements",
      value: summary.kol_engagements ?? 0,
      color: palette.cream,
      bg: `${palette.cream}10`,
    },
    {
      label: "Estimated Revenue",
      value: `$${summary.estimated_revenue_impact ?? 0}`,
      color: palette.accent,
      bg: `${palette.accent}10`,
    },
    {
      label: "Coverage Improvement",
      value: summary.estimated_coverage_improvement ?? "0%",
      color: "#7C6C94",
      bg: "#7C6C9410",
    },
  ];

  return (
    <Card
      sx={{
        height: "100%",
        borderRadius: "24px",
        backgroundColor: palette.surface,
        border: `1px solid ${palette.border}`,
        boxShadow: "0px 8px 32px rgba(43,35,56,0.05)",
      }}
    >
      <CardContent sx={{ p: 3 }}>
        {/* Header */}
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="flex-start"
          sx={{ mb: 3 }}
        >
          <Box>
            <Typography
              sx={{
                fontFamily: "Sora",
                fontWeight: 700,
                fontSize: "1.5rem",
                color: palette.text,
                mb: 0.75,
              }}
            >
              Today's AI Plan
            </Typography>

            <Typography
              sx={{
                color: palette.textMuted,
                maxWidth: 650,
                fontSize: "0.9rem",
                lineHeight: 1.6,
              }}
            >
              Prioritized daily execution actions powered by existing
              opportunity and conversion signals.
            </Typography>
          </Box>

          <Button
            variant="contained"
            onClick={onReplan}
            disabled={loading || !onReplan}
            data-testid="daily-plan-replan"
            sx={{
              textTransform: "none",
              px: 3,
              py: 1,
              minWidth: 110,
              borderRadius: "999px",
              fontWeight: 600,
              color: "#fff",
              background: `linear-gradient(135deg, ${palette.primary} 0%, ${palette.accent} 100%)`,
              boxShadow: "0px 8px 18px rgba(83,70,102,0.25)",

              "&:hover": {
                background: `linear-gradient(135deg, ${palette.primaryDark} 0%, ${palette.accent} 100%)`,
              },
            }}
          >
            {loading ? (
              <CircularProgress size={18} color="inherit" />
            ) : (
              "Replan"
            )}
          </Button>
        </Stack>

        {/* Chips */}
        <Stack direction="row" spacing={1.5} sx={{ mb: 4 }}>
          <Chip
            label="Smart Day Planner"
            size="medium"
            sx={{
              bgcolor: `${palette.accent}15`,
              color: palette.accent,
              borderRadius: "999px",
              fontWeight: 600,
              border: `1px solid ${palette.accent}25`,
            }}
          />

          <Chip
            label="AI-generated priorities"
            size="medium"
            sx={{
              bgcolor: `${palette.light}15`,
              color: palette.light,
              borderRadius: "999px",
              fontWeight: 600,
              border: `1px solid ${palette.light}25`,
            }}
          />
        </Stack>

        {/* KPI Grid */}
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 2,
          }}
        >
          {metrics.map((item) => (
            <Box
              key={item.label}
              sx={metricCardStyle(item.color, item.bg)}
            >
              <Typography
                sx={{
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: palette.textMuted,
                }}
              >
                {item.label}
              </Typography>

              <Typography
                sx={{
                  fontWeight: 700,
                  fontSize: "2.15rem",
                  color: item.color,
                  lineHeight: 1.1,
                  mt: 2,
                }}
              >
                {item.value}
              </Typography>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
}