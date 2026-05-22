import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, Grid, Typography, Stack, Chip, Tab, Tabs,
} from "@mui/material";
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ComposedChart,
} from "recharts";
import { Conversion } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import KPICard from "../components/KPICard";
import LoadingState from "../components/LoadingState";
import { palette, chartPalette } from "../theme/kiwiTheme";

export default function ConversionAnalytics() {
  const [trend, setTrend] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [overview, setOverview] = useState(null);
  const [byRep, setByRep] = useState([]);
  const [byTherapy, setByTherapy] = useState([]);
  const [heat, setHeat] = useState(null);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    Conversion.overview().then(setOverview);
    Conversion.trend("W").then(setTrend);
    Conversion.forecast(8).then(setForecast);
    Conversion.breakdown("rep_name").then(setByRep);
    Conversion.breakdown("specialty_group").then(setByTherapy);
    Conversion.heatmap().then(setHeat);
  }, []);

  if (!overview || !trend.length) return <LoadingState label="Loading conversion analytics…" />;

  const trendWithForecast = [
    ...trend.map((t) => ({ ...t, forecast: null })),
    ...forecast.map((f) => ({
      bucket: f.bucket, total_calls: null, conversion_rate: null,
      rolling_7d: null, rolling_30d: null,
      forecast: f.forecast_rate, low: f.confidence_low, high: f.confidence_high,
    })),
  ];

  return (
    <Box>
      <SectionHeader
        eyebrow="ConversionRate_30d Engine"
        title="Conversion Analytics"
        subtitle="Real-time rolling 30-day conversion attribution with breakdowns, heatmap, and forward-looking forecast."
      />

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

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
            <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Conversion Trend with 8-week Forecast</Typography>
            <Stack direction="row" spacing={1}>
              <Chip size="small" label="Actual rate" sx={{ bgcolor: "rgba(2,129,116,0.12)", color: palette.primary }} />
              <Chip size="small" label="30d rolling" sx={{ bgcolor: "rgba(146,222,139,0.4)", color: palette.primaryDark }} />
              <Chip size="small" label="Forecast" sx={{ bgcolor: palette.cream, color: palette.primaryDark }} />
            </Stack>
          </Stack>
          <Box sx={{ height: 340 }}>
            <ResponsiveContainer>
              <ComposedChart data={trendWithForecast}>
                <defs>
                  <linearGradient id="conv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={palette.primary} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={palette.primary} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                <XAxis dataKey="bucket" tickFormatter={(v) => v?.slice(5, 10)} tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} unit="%" />
                <Tooltip />
                <Legend />
                <Area dataKey="rolling_30d" stroke={palette.light} fill="url(#conv)" strokeWidth={2} />
                <Line dataKey="rolling_7d" stroke={palette.primary} strokeWidth={2.5} dot={false} />
                <Line dataKey="forecast" stroke={palette.cream} strokeWidth={3} strokeDasharray="5 5" dot={{ fill: palette.cream, r: 3 }} />
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
