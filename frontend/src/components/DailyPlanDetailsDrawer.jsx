import React from "react";
import { Drawer, Box, Typography, Stack, Chip, Divider } from "@mui/material";
import { palette } from "../theme/kiwiTheme";

export default function DailyPlanDetailsDrawer({ open, action, onClose }) {
  if (!action) return null;
  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 420, p: 3 }}>
        <Stack spacing={2}>
          <Stack spacing={0.5}>
            <Typography variant="h6">{action.title}</Typography>
            <Typography variant="body2" color="text.secondary">{action.scheduled_time} · {action.duration_minutes} min · {action.action_type}</Typography>
          </Stack>
          <Chip label={action.priority} sx={{ bgcolor: palette.accent, color: "#fff", width: "fit-content" }} />
          <Divider />
          <Box>
            <Typography variant="subtitle2">Why recommended?</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>{action.nba_rationale}</Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2">Expected outcome</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>{action.expected_outcome}</Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2">Plan details</Typography>
            <Stack spacing={1} sx={{ mt: 1 }}>
              <Typography variant="body2"><strong>HCP:</strong> {action.hcp_name}</Typography>
              <Typography variant="body2"><strong>Account:</strong> {action.account}</Typography>
              <Typography variant="body2"><strong>Therapy Area:</strong> {action.therapy_area}</Typography>
              <Typography variant="body2"><strong>Product Focus:</strong> {action.product_focus}</Typography>
              <Typography variant="body2"><strong>Conversion probability:</strong> {action.conversion_probability}%</Typography>
            </Stack>
          </Box>
          <Box>
            <Typography variant="subtitle2">Explainability</Typography>
            <Stack spacing={1} sx={{ mt: 1 }}>
              {Object.entries(action.details.drivers || {}).map(([label, value]) => (
                <Typography key={label} variant="body2" color="text.secondary">
                  <strong>{label.replace(/_/g, " ")}:</strong> {value}
                </Typography>
              ))}
            </Stack>
          </Box>
        </Stack>
      </Box>
    </Drawer>
  );
}
