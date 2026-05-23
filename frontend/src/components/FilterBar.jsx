import React, { useEffect, useState } from "react";
import {
  Card, CardContent, Stack, Typography, Chip, FormControl, InputLabel, Select, MenuItem,
  IconButton, Tooltip as MTooltip,
} from "@mui/material";
import RestartAltRoundedIcon from "@mui/icons-material/RestartAltRounded";
import { ExecDash } from "../services/api";
import { palette } from "../theme/kiwiTheme";

/**
 * Shared filter bar used by Executive, Conversion, and KOL pages.
 *
 * Props:
 *   value: { specialty, territory, region, time_window_days }
 *   onChange(next): called when any filter changes
 *   show: { specialty, territory, region, time_window_days } — which to show (default: all)
 *   testidPrefix: data-testid prefix for selects
 */
export default function FilterBar({
  value,
  onChange,
  show = { specialty: true, territory: true, region: true, time_window_days: true },
  testidPrefix = "filter",
}) {
  const [opts, setOpts] = useState({ specialties: [], territories: [], regions: [], time_windows: [] });

  useEffect(() => { ExecDash.filters().then(setOpts).catch(() => {}); }, []);

  const update = (k, v) => onChange({ ...value, [k]: v });
  const reset = () => onChange({ specialty: "", territory: "", region: "", time_window_days: "" });
  const activeCount = Object.values(value || {}).filter(Boolean).length;

  return (
    <Card sx={{ mb: 2.5 }} data-testid={`${testidPrefix}-bar`}>
      <CardContent sx={{ py: 1.5 }}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.2} alignItems={{ md: "center" }}>
          <Typography variant="overline" sx={{ color: palette.textMuted, mr: 1 }}>Filters</Typography>

          {show.specialty && (
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Specialty</InputLabel>
              <Select
                label="Specialty"
                value={value.specialty || ""}
                onChange={(e) => update("specialty", e.target.value)}
                data-testid={`${testidPrefix}-specialty`}
              >
                <MenuItem value=""><em>All</em></MenuItem>
                {opts.specialties.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
          )}

          {show.territory && (
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Territory</InputLabel>
              <Select
                label="Territory"
                value={value.territory || ""}
                onChange={(e) => update("territory", e.target.value)}
                data-testid={`${testidPrefix}-territory`}
              >
                <MenuItem value=""><em>All</em></MenuItem>
                {opts.territories.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
          )}

          {show.region && (
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Region</InputLabel>
              <Select
                label="Region"
                value={value.region || ""}
                onChange={(e) => update("region", e.target.value)}
                data-testid={`${testidPrefix}-region`}
              >
                <MenuItem value=""><em>All</em></MenuItem>
                {opts.regions.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
          )}

          {show.time_window_days && (
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Time window</InputLabel>
              <Select
                label="Time window"
                value={value.time_window_days || ""}
                onChange={(e) => update("time_window_days", e.target.value)}
                data-testid={`${testidPrefix}-time`}
              >
                <MenuItem value=""><em>All time</em></MenuItem>
                {opts.time_windows.filter((w) => w.value > 0).map((w) => (
                  <MenuItem key={w.value} value={w.value}>{w.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          <Stack sx={{ flex: 1 }} />
          {activeCount > 0 && (
            <Chip
              label={`${activeCount} filter${activeCount > 1 ? "s" : ""} active`}
              size="small"
              sx={{ bgcolor: palette.cream, color: palette.primaryDark, fontWeight: 700 }}
              data-testid={`${testidPrefix}-active-count`}
            />
          )}
          <MTooltip title="Reset filters">
            <span>
              <IconButton
                size="small"
                onClick={reset}
                disabled={activeCount === 0}
                data-testid={`${testidPrefix}-reset`}
              >
                <RestartAltRoundedIcon fontSize="small" />
              </IconButton>
            </span>
          </MTooltip>
        </Stack>
      </CardContent>
    </Card>
  );
}

/** Build a clean params object from a filter state, dropping empty values. */
export function buildFilterParams(value) {
  const out = {};
  if (value?.specialty) out.specialty = value.specialty;
  if (value?.territory) out.territory = value.territory;
  if (value?.region) out.region = value.region;
  if (value?.time_window_days) out.time_window_days = value.time_window_days;
  return out;
}

export const EMPTY_FILTERS = { specialty: "", territory: "", region: "", time_window_days: "" };
