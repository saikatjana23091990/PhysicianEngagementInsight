import React from "react";
import { Box, Typography, Stack } from "@mui/material";
import { palette } from "../theme/kiwiTheme";

export default function SectionHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ md: "flex-end" }} spacing={2} sx={{ mb: 3 }}>
      <Box>
        {eyebrow && (
          <Typography variant="overline" sx={{ color: palette.accent, letterSpacing: "0.18em" }}>
            {eyebrow}
          </Typography>
        )}
        <Typography variant="h3" sx={{ fontFamily: "Sora" }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body1" sx={{ color: palette.textMuted, mt: 0.5, maxWidth: 720 }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      {actions && <Box>{actions}</Box>}
    </Stack>
  );
}
