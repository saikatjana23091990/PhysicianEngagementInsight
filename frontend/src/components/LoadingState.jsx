import React from "react";
import { Box, CircularProgress, Typography } from "@mui/material";

export default function LoadingState({ label = "Loading…" }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, py: 4, justifyContent: "center" }}>
      <CircularProgress size={20} thickness={5} />
      <Typography variant="body2" color="text.secondary">{label}</Typography>
    </Box>
  );
}
