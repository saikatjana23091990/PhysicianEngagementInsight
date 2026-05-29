import React from "react";
import { Card, CardContent, Stack, Typography, Box, Chip } from "@mui/material";
import { palette } from "../theme/kiwiTheme";

export default function ExecutionCopilotWidget({ narrative }) {
  if (!narrative) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>AI Coach</Typography>
          <Typography variant="body2" color="text.secondary">Loading execution guidance...</Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" sx={{ fontFamily: "Sora" }}>AI Coach</Typography>
          <Box sx={{ p: 2, bgcolor: palette.surfaceAlt, borderRadius: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Morning Brief</Typography>
            <Typography variant="body2" color="text.secondary">{narrative.morning_brief}</Typography>
          </Box>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Chip label="Today Focus" sx={{ bgcolor: palette.accent, color: "#fff" }} />
            <Chip label="Mid-Day Review" sx={{ bgcolor: palette.primary, color: "#fff" }} />
            <Chip label="EOD Summary" sx={{ bgcolor: palette.light, color: "#fff" }} />
          </Stack>
          <Box>
            <Typography variant="subtitle2">Top Focus Areas</Typography>
            {Array.isArray(narrative.today_focus) && narrative.today_focus.length ? (
              <Stack spacing={1} sx={{ mt: 1 }}>
                {narrative.today_focus.map((item, index) => (
                  <Typography key={index} variant="body2" color="text.secondary">• {item}</Typography>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">No additional focus areas were generated.</Typography>
            )}
          </Box>
          <Box>
            <Typography variant="subtitle2">Mid-Day Review</Typography>
            <Typography variant="body2" color="text.secondary">{narrative.midday_review}</Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
