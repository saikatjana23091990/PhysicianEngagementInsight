import React from "react";
import { Card, CardContent, Typography, Stack } from "@mui/material";

export default function PriorityChangeFeed({ items = [] }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Priority Change Feed</Typography>
        {items.length ? (
          <Stack spacing={1}>
            {items.map((item, index) => (
              <Typography key={index} variant="body2" color="text.secondary">
                • {item.message}
              </Typography>
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">No priority changes yet. The plan is stable for today.</Typography>
        )}
      </CardContent>
    </Card>
  );
}
