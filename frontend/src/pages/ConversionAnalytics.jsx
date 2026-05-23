import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, Grid, Typography, Stack, Chip, Tab, Tabs,
} from "@mui/material";
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Cell, ComposedChart, ReferenceLine, ReferenceArea,
} from "recharts";
import { Conversion } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import KPICard from "../components/KPICard";
import LoadingState from "../components/LoadingState";
import { palette, chartPalette } from "../theme/kiwiTheme";
import FilterBar, { buildFilterParams, EMPTY_FILTERS } from "../components/FilterBar";

export default function ConversionAnalytics() {
  const [trend, setTrend] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [overview, setOverview] = useState(null);
  const [byRep, setByRep] = useState([]);
  const [byTherapy, setByTherapy] = useState([]);
  const [heat, setHeat] = useState(null);
  const [tab, setTab] = useState(0);
  const [filters, setFilters] = useState(EMPTY_FILTERS);

  useEffect(() => {
    const p = buildFilterParams(filters);
    setOverview(null);
    setForecast(null);
    Conversion.overview(p).then(setOverview);
    Conversion.trend("W", p).then(setTrend);
    Conversion.forecast(8, p).then(setForecast);
    Conversion.breakdown("rep_name", p).then(setByRep);
    Conversion.breakdown("specialty_group", p).then(setByTherapy);
    Conversion.heatmap(p).then(setHeat);
  }, [filters]);

  if (!overview || !forecast) return (
    <Box>
      <SectionHeader
        eyebrow="ConversionRate_30d Engine"
        title="Conversion Analytics"
        subtitle="Real-time rolling 30-day conversion attribution with breakdowns, heatmap, and forward-looking forecast."
      />
      <FilterBar value={filters} onChange={setFilters} testidPrefix="conv-filter" />
      <LoadingState label="Loading conversion analytics…" />
    </Box>
  );

  // Build combined volume chart (history + forecast for total_calls vs converted_calls)
  const volumeData = [
    ...forecast.history.map((h) => ({
      bucket: h.bucket,
      total_calls: h.total_calls,
      converted_calls: h.converted_calls,
    })),
    ...forecast.forecast.map((f) => ({
      bucket: f.bucket,
      total_forecast: f.total_forecast,
      total_band: [f.total_low, f.total_high],
      converted_forecast: f.converted_forecast,
      converted_band: [f.converted_low, f.converted_high],
    })),
  ];
  const convBucket = forecast.convergence?.bucket;
  const direction = forecast.convergence?.direction;

  return (
    <Box>
      <SectionHeader
        eyebrow="ConversionRate_30d Engine"
        title="Conversion Analytics"
        subtitle="Real-time rolling 30-day conversion attribution with breakdowns, heatmap, and forward-looking forecast."
      />

      <FilterBar value={filters} onChange={setFilters} testidPrefix="conv-filter" />

      <Grid container spacing={2.5} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard testid="conv-rate" label="Current rate" value={overview.conversion_rate?.toFixed(1)} unit="%"
            sublabel="vs target 12%" delta={overview.uplift_vs_target} trend={overview.uplift_vs_target >= 0 ? "up" : "down"} accent={palette.primary}/>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard label="Total calls" value={overview.total_calls} accent={palette.accent}/>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard label="Converted calls" value={overview.converted_calls} accent={palette.light}/>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard label="Target" value="12" unit="%" sublabel="QoQ uplift +2% goal" accent={palette.cream}/>
        </Grid>
      </Grid>

      <Card sx={{ mb: 2 }} data-testid="forecast-chart">
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
            <Box>
              <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Total Calls vs Converted Calls — 8-week Forecast</Typography>
              <Typography variant="caption" sx={{ color: palette.textMuted }}>
                The gap between the two lines is the conversion opportunity. Watch for narrowing (improving) vs widening (worsening).
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Chip size="small" label="Total calls" sx={{ bgcolor: "rgba(2,129,116,0.12)", color: palette.primary, fontWeight: 700 }} />
              <Chip size="small" label="Converted calls" sx={{ bgcolor: "rgba(10,182,139,0.18)", color: palette.primary, fontWeight: 700 }} />
              <Chip size="small" label="Forecast band" sx={{ bgcolor: palette.cream, color: palette.primaryDark, fontWeight: 700 }} />
            </Stack>
          </Stack>
          {forecast.convergence && (
            <Stack direction="row" spacing={1.5} alignItems="center" sx={{ my: 1.5, p: 1.5, bgcolor: palette.surfaceAlt, borderRadius: 2 }}>
              <Box sx={{ width: 10, height: 10, borderRadius: "50%",
                bgcolor: direction === "narrowing" ? palette.accent : direction === "widening" ? palette.danger : palette.cream }} />
              <Typography variant="body2">
                <b>Trend is {direction}.</b> Current gap: <b>{forecast.convergence.current_gap}</b> calls/week ·
                Forecast min gap: <b>{forecast.convergence.min_gap?.toFixed(1)}</b> at <b>{convBucket?.slice(0, 10)}</b>
              </Typography>
            </Stack>
          )}
          <Box sx={{ height: 360 }}>
            <ResponsiveContainer>
              <ComposedChart data={volumeData}>
                <defs>
                  <linearGradient id="totalArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={palette.primary} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={palette.primary} stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="convArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={palette.accent} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={palette.accent} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                <XAxis dataKey="bucket" tickFormatter={(v) => v?.slice(5, 10)} tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                {/* Historical actuals */}
                <Area type="monotone" dataKey="total_calls" stroke={palette.primary} fill="url(#totalArea)" strokeWidth={2.5} name="Total calls (actual)" />
                <Area type="monotone" dataKey="converted_calls" stroke={palette.accent} fill="url(#convArea)" strokeWidth={2.5} name="Converted calls (actual)" />
                {/* Forecast confidence bands */}
                <Area type="monotone" dataKey="total_band" stroke="none" fill={palette.primary} fillOpacity={0.08} name="Total band" legendType="none" />
                <Area type="monotone" dataKey="converted_band" stroke="none" fill={palette.accent} fillOpacity={0.1} name="Converted band" legendType="none" />
                {/* Forecast lines (dashed) */}
                <Line type="monotone" dataKey="total_forecast" stroke={palette.primary} strokeWidth={2.5} strokeDasharray="5 4" dot={{ fill: palette.primary, r: 3 }} name="Total (forecast)" />
                <Line type="monotone" dataKey="converted_forecast" stroke={palette.accent} strokeWidth={2.5} strokeDasharray="5 4" dot={{ fill: palette.accent, r: 3 }} name="Converted (forecast)" />
                {convBucket && (
                  <ReferenceLine x={convBucket} stroke={palette.cream} strokeWidth={2}
                    label={{ value: "Min-gap week", position: "top", fill: palette.primaryDark, fontSize: 11, fontWeight: 700 }} />
                )}
                {/* Forecast region tint */}
                {forecast.forecast.length > 0 && (
                  <ReferenceArea x1={forecast.forecast[0].bucket} x2={forecast.forecast.slice(-1)[0].bucket}
                    fill={palette.cream} fillOpacity={0.18} />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
            <Tab label="By Therapy Area" />
            <Tab label="By Rep" />
            <Tab label="Heatmap (Rep × Therapy)" />
          </Tabs>
          {tab === 0 && (
            <Box sx={{ height: 360 }}>
              <ResponsiveContainer>
                <BarChart data={byTherapy} layout="vertical" margin={{ left: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                  <XAxis type="number" tick={{ fontSize: 12 }} unit="%" />
                  <YAxis type="category" dataKey="specialty_group" tick={{ fontSize: 12 }} width={140} />
                  <Tooltip formatter={(v) => v?.toFixed?.(1) + "%"} />
                  <Bar dataKey="conversion_rate" radius={[0, 8, 8, 0]}>
                    {byTherapy.map((_, i) => <Cell key={i} fill={chartPalette[i % chartPalette.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Box>
          )}
          {tab === 1 && (
            <Box sx={{ height: Math.max(360, byRep.length * 28) }}>
              <ResponsiveContainer>
                <BarChart data={byRep} layout="vertical" margin={{ left: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                  <XAxis type="number" tick={{ fontSize: 12 }} unit="%" />
                  <YAxis type="category" dataKey="rep_name" tick={{ fontSize: 11 }} width={140} />
                  <Tooltip formatter={(v) => v?.toFixed?.(1) + "%"} />
                  <Bar dataKey="conversion_rate" fill={palette.accent} radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          )}
          {tab === 2 && heat && (
            <HeatmapGrid rows={heat.rows} columns={heat.columns} matrix={heat.matrix} />
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

function HeatmapGrid({ rows, columns, matrix }) {
  if (!matrix?.length) return <Typography sx={{ color: palette.textMuted }}>No data</Typography>;
  const max = Math.max(...matrix.flat().filter(Number.isFinite));
  return (
    <Box sx={{ overflowX: "auto" }} data-testid="conversion-heatmap">
      <Box sx={{ display: "inline-grid", gridTemplateColumns: `160px repeat(${columns.length}, minmax(70px, 1fr))`, gap: 0.5 }}>
        <Box />
        {columns.map((c) => (
          <Box key={c} sx={{ fontSize: 11, fontWeight: 700, color: palette.textMuted, textAlign: "center", py: 0.5 }}>
            {c}
          </Box>
        ))}
        {rows.map((rep, ri) => (
          <React.Fragment key={rep}>
            <Box sx={{ fontSize: 12, fontWeight: 600, py: 0.5 }}>{rep}</Box>
            {columns.map((_, ci) => {
              const v = matrix[ri][ci] || 0;
              const t = max > 0 ? v / max : 0;
              return (
                <Box key={ci} sx={{
                  height: 36,
                  bgcolor: `rgba(2, 129, 116, ${0.06 + t * 0.85})`,
                  color: t > 0.55 ? "#fff" : palette.primaryDark,
                  display: "grid", placeItems: "center",
                  borderRadius: 1, fontSize: 11, fontWeight: 700, fontFamily: "JetBrains Mono",
                }}>
                  {v > 0 ? v.toFixed(0) + "%" : "—"}
                </Box>
              );
            })}
          </React.Fragment>
        ))}
      </Box>
    </Box>
  );
}
