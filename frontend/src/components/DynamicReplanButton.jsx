import React from "react";
import { Button } from "@mui/material";

export default function DynamicReplanButton({ onClick, loading }) {
  return (
    <Button variant="contained" color="primary" onClick={onClick} disabled={loading}>
      {loading ? "Refreshing..." : "Replan"}
    </Button>
  );
}
