import React from "react";
import { Box, Typography, Chip, Stack } from "@mui/material";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import { palette } from "../theme/kiwiTheme";

const priorityColorMap = {
  Critical: {
    dot: palette.danger,
    chip: palette.danger,
    chipText: "#fff",
  },
  High: {
    dot: palette.light,
    chip: palette.light,
    chipText: "#fff",
  },
  Medium: {
    dot: palette.accent,
    chip: palette.accent,
    chipText: "#fff",
  },
  Low: {
    dot: palette.surfaceAlt,
    chip: palette.surfaceAlt,
    chipText: palette.text,
  },
};

export default function DailyPlanTimeline({ actions, onSelect }) {
  if (!actions || !actions.length) {
    return (
      <Box
        sx={{
          p: 3,
          borderRadius: 3,
          bgcolor: "rgba(20,20,20,0.02)",
        }}
      >
        <Typography variant="body2" color="text.secondary">
          No plan actions available for today.
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        maxHeight: 520,
        overflowY: "auto",
        pr: 1,
        bgcolor: palette.surface,
      }}
    >
      <Box
        sx={{
          position: "relative",
          py: 2,
          px: 2,
        }}
      >
        {/* Timeline Vertical Line */}
        <Box
          sx={{
            position: "absolute",
            left: 92,
            top: 20,
            bottom: 20,
            width: 2,
            bgcolor: "rgba(0,0,0,0.08)",
          }}
        />

        <Stack spacing={4}>
          {actions.map((action) => (
            <Box
              key={action.action_id}
              sx={{
                position: "relative",
                minHeight: 110,
              }}
            >
              {/* Time */}
              <Typography
                variant="caption"
                sx={{
                  position: "absolute",
                  left: 0,
                  top: 10,
                  width: 70,
                  textAlign: "right",
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  color: palette.primary,
                }}
              >
                {action.scheduled_time}
              </Typography>

              {/* Timeline Dot */}
              <Box
                sx={{
                  position: "absolute",
                  left: 75,
                  top: 4,
                  width: 34,
                  height: 34,
                  borderRadius: "50%",
                  bgcolor:
                    priorityColorMap[action.priority]?.dot ||
                    palette.surfaceAlt,

                  border: `3px solid ${palette.bg}`,

                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",

                  boxShadow: "0 2px 8px rgba(0,0,0,0.12)",

                  zIndex: 2,
                }}
              >
                <ScheduleRoundedIcon
                  sx={{
                    fontSize: 18,
                    color: "#fff",
                  }}
                />
              </Box>

              {/* Content Card */}
              <Box
                onClick={() => onSelect?.(action)}
                sx={{
                  ml: "130px",

                  p: 3,

                  borderRadius: 1,

                  bgcolor: palette.surface,

                  border: `1px solid ${
                    palette.surfaceAlt || "rgba(0,0,0,0.08)"
                  }`,

                  boxShadow: "0 1px 4px rgba(0,0,0,0.06)",

                  cursor: onSelect ? "pointer" : "default",

                  transition: "all 180ms ease",

                  "&:hover": {
                    transform: "translateY(-2px)",
                    boxShadow: "0 8px 24px rgba(0,0,0,0.10)",
                  },
                }}
              >
                {/* Header */}
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="flex-start"
                  spacing={2}
                  sx={{ mb: 2 }}
                >
                  <Typography
                    variant="subtitle1"
                    sx={{
                      fontWeight: 700,
                      flex: 1,
                    }}
                  >
                    {action.title}
                  </Typography>

                  <Chip
                    size="small"
                    label={action.priority}
                    sx={{
                      bgcolor:
                        priorityColorMap[action.priority]?.chip ||
                        palette.surfaceAlt,

                      color:
                        priorityColorMap[action.priority]?.chipText ||
                        palette.text,

                      fontWeight: 700,

                      height: 28,

                      borderRadius: "14px",

                      px: 1,
                    }}
                  />
                </Stack>

                {/* HCP + Account */}
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1 }}
                >
                  {action.hcp_name} • {action.account}
                </Typography>

                {/* Duration + Confidence */}
                <Stack
                  direction="row"
                  spacing={2}
                  sx={{ mb: 1 }}
                >
                  <Typography
                    variant="caption"
                    color="text.secondary"
                  >
                    {action.duration_minutes} min
                  </Typography>

                  <Typography
                    variant="caption"
                    color="text.secondary"
                  >
                    {action.confidence_score}% confidence
                  </Typography>
                </Stack>

                {/* Outcome */}
                <Typography
                  variant="body2"
                  color="text.secondary"
                >
                  {action.expected_outcome}
                </Typography>
              </Box>
            </Box>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}