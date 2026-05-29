import React from "react";
import { Card, CardContent, Typography, Stack, Chip, Box } from "@mui/material";
import { palette } from "../theme/kiwiTheme";

const priorityColors = {
  Critical: palette.danger,
  High: palette.light,
  Medium: palette.accent,
  Low: palette.surfaceAlt,
};

export default function DailyPlanCard({ action, onClick }) {
  const priorityColor = priorityColors[action.priority] || palette.accent;
  return (
    <Card
      onClick={onClick}
      sx={{
        minWidth: 260,
        cursor: "pointer",
        borderRadius: 3,
        transition: "transform 160ms ease",
        '&:hover': { transform: "translateY(-3px)" },
      }}
      data-testid="daily-plan-card"
    >
      <CardContent>
        <Stack spacing={1}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="subtitle2" color="text.secondary">{action.scheduled_time}</Typography>
            <Chip
              label={action.priority}
              size="small"
              sx={{
                bgcolor: priorityColor,
                color: action.priority === "Low" ? palette.text : "#fff",
                fontWeight: 700,
              }}
            />
          </Stack>

          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{action.title}</Typography>
          <Typography variant="body2" color="text.secondary" noWrap>{action.hcp_name} · {action.account}</Typography>

          <Box sx={{ display: "grid", gap: 4, gridTemplateColumns: "repeat(2, minmax(0, 1fr))", pt: 1 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Duration</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700 }}>{action.duration_minutes} min</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Confidence</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700 }}>{action.confidence_score}%</Typography>
            </Box>
          </Box>

          <Typography variant="body2" sx={{ mt: 1, color: palette.primaryDark }}>{action.expected_outcome}</Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
