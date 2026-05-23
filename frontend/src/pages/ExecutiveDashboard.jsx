import React, { useEffect, useState } from "react";
import {
  Grid, Card, CardContent, Typography, Box, Stack, Chip, Button, Divider, Paper,
  Table, TableHead, TableRow, TableCell, TableBody, LinearProgress,
} from "@mui/material";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import PictureAsPdfRoundedIcon from "@mui/icons-material/PictureAsPdfRounded";
import ReactMarkdown from "react-markdown";
import {
  AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, BarChart, Bar, CartesianGrid, Legend, Cell,
} from "recharts";
import { ExecDash, Export } from "../services/api";
import { chartPalette, palette } from "../theme/kiwiTheme";
import KPICard from "../components/KPICard";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import FilterBar, { buildFilterParams, EMPTY_FILTERS } from "../components/FilterBar";

export default function ExecutiveDashboard() {
  const [data, setData] = useState(null);
  const [narrative, setNarrative] = useState(null);
  const [narrLoading, setNarrLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [filters, setFilters] = useState(EMPTY_FILTERS);

  useEffect(() => {
    setData(null);
    ExecDash.dashboard(buildFilterParams(filters)).then(setData).catch(console.error);
  }, [filters]);

  const generateNarrative = async () => {
    setNarrLoading(true);
    try {
      const n = await ExecDash.narrative();
      setNarrative(n);
    } catch (e) {
      setNarrative({ narrative_markdown: "Could not generate narrative. " + e.message });
    } finally {
      setNarrLoading(false);
    }
  };

  const downloadPdf = async () => {
    setPdfLoading(true);
    try {
      await Export.execBriefPdf(true);
    } catch (e) {
      alert("PDF export failed: " + e.message);
    } finally {
      setPdfLoading(false);
    }
  };

  if (!data) return <LoadingState label="Loading executive view…" />;

  const conv = data.conversion;
  return (
    <Box>
      <SectionHeader
        eyebrow="Commercial Leadership"
        title="Executive Dashboard"
        subtitle="Engagement-to-Conversion across the field force, with AI-generated narrative and KOL signals."
        actions={
          <Stack direction="row" spacing={1}>
            <Button
              data-testid="exec-pdf-btn"
              variant="outlined"
              startIcon={<PictureAsPdfRoundedIcon />}
              onClick={downloadPdf}
              disabled={pdfLoading}
              sx={{
                borderColor: palette.primary, color: palette.primary,
                "&:hover": { borderColor: palette.primaryDark, bgcolor: "rgba(2,129,116,0.06)" },
              }}
            >
              {pdfLoading ? "Generating PDF…" : "Export Brief (PDF)"}
            </Button>
            <Button
              data-testid="exec-narrative-btn"
              variant="contained"
              startIcon={<AutoAwesomeRoundedIcon />}
              onClick={generateNarrative}
              disabled={narrLoading}
            >
              {narrLoading ? "Generating…" : "Generate AI Narrative"}
            </Button>
          </Stack>
        }
      />

      {/* Filter bar */}
      <FilterBar value={filters} onChange={setFilters} testidPrefix="exec-filter" />

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            testid="kpi-conversion"
            label="ConversionRate_30d"
            value={conv.conversion_rate?.toFixed(1)}
            unit="%"
            sublabel={`Target 12% · ${conv.converted_calls}/${conv.total_calls} calls`}
            delta={(conv.conversion_rate - 12).toFixed(1)}
            trend={conv.conversion_rate >= 12 ? "up" : "down"}
            accent={palette.primary}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            testid="kpi-avg-confidence"
            label="Attribution Confidence"
            value={(conv.avg_confidence * 100).toFixed(0)}
            unit="%"
            sublabel="Avg across linked calls"
            accent={palette.accent}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            testid="kpi-kols"
            label="KOLs Tracked"
            value={data.kol_summary.total_kols}
            sublabel={`Tier 1: ${data.kol_summary.tier1} · Rising: ${data.kol_summary.rising_stars}`}
            accent={palette.light}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            testid="kpi-top-opp"
            label="Top Opportunity"
            value={data.top_opportunities[0]?.opportunity_score?.toFixed(0) || "—"}
            unit="pts"
            sublabel={data.top_opportunities[0]?.hcp_name || ""}
            accent={palette.cream}
          />
        </Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid item xs={12} lg={8}>
          <Card data-testid="conversion-trend-card">
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                <Box>
                  <Typography variant="overline" sx={{ color: palette.textMuted }}>
                    Weekly trend
                  </Typography>
                  <Typography variant="h5" sx={{ fontFamily: "Sora" }}>
                    Conversion Rate (30-day window)
                  </Typography>
                </Box>
                <Stack direction="row" spacing={1}>
                  <Chip size="small" label="Rolling 7d" sx={{ bgcolor: "rgba(10,182,139,0.15)", color: palette.primary }} />
                  <Chip size="small" label="Rolling 30d" sx={{ bgcolor: "rgba(146,222,139,0.4)", color: palette.primaryDark }} />
                </Stack>
              </Stack>
              <Box sx={{ height: 320 }}>
                <ResponsiveContainer>
                  <AreaChart data={data.trend} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={palette.primary} stopOpacity={0.45} />
                        <stop offset="100%" stopColor={palette.primary} stopOpacity={0.02} />
                      </linearGradient>
                      <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={palette.light} stopOpacity={0.6} />
                        <stop offset="100%" stopColor={palette.light} stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                    <XAxis dataKey="bucket" tickFormatter={(v) => v.slice(5, 10)} tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} unit="%" />
                    <Tooltip formatter={(v) => (typeof v === "number" ? v.toFixed(1) + "%" : v)} />
                    <Area type="monotone" dataKey="rolling_30d" stroke={palette.light} fill="url(#g2)" strokeWidth={2} />
                    <Area type="monotone" dataKey="rolling_7d" stroke={palette.primary} fill="url(#g1)" strokeWidth={2.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card sx={{ height: "100%" }} data-testid="ai-narrative-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <AutoAwesomeRoundedIcon sx={{ color: palette.accent }} />
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>
                  AI Executive Narrative
                </Typography>
              </Stack>
              {narrLoading && <LinearProgress sx={{ mb: 1, borderRadius: 2 }} />}
              {!narrative && (
                <Typography variant="body2" sx={{ color: palette.textMuted }}>
                  Click "Generate AI Narrative" to produce a grounded, source-cited commentary
                  explaining KPI movement, leaders, laggards, and 30-day actions.
                </Typography>
              )}
              {narrative && (
                <>
                  <Box sx={{ "& p": { mt: 1.2, mb: 0 }, "& h2": { fontFamily: "Sora", fontSize: 16, mt: 2 } }}>
                    <ReactMarkdown>{narrative.narrative_markdown}</ReactMarkdown>
                  </Box>
                  <Divider sx={{ my: 1.5 }} />
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    <Chip size="small" label={`Provider: ${narrative.provider}`} sx={{ bgcolor: palette.surfaceAlt }} />
                    <Chip size="small" label={`${narrative.latency_ms} ms`} sx={{ bgcolor: palette.surfaceAlt }} />
                    {narrative.fallback_used && <Chip size="small" label="fallback" color="warning" />}
                  </Stack>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>By Therapy Area</Typography>
              <Box sx={{ height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={data.by_specialty} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                    <XAxis type="number" tick={{ fontSize: 12 }} unit="%" />
                    <YAxis type="category" dataKey="specialty_group" tick={{ fontSize: 12 }} width={120} />
                    <Tooltip formatter={(v) => v.toFixed(1) + "%"} />
                    <Bar dataKey="conversion_rate" radius={[0, 8, 8, 0]}>
                      {data.by_specialty.map((_, i) => (
                        <Cell key={i} fill={chartPalette[i % chartPalette.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>By Territory</Typography>
              <Box sx={{ height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={data.by_territory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                    <XAxis dataKey="territory" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} unit="%" />
                    <Tooltip formatter={(v) => v.toFixed(1) + "%"} />
                    <Bar dataKey="conversion_rate" fill={palette.accent} radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card data-testid="top-opportunities-card">
            <CardContent>
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Top Opportunities</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>HCP</TableCell>
                    <TableCell>Specialty</TableCell>
                    <TableCell>Territory</TableCell>
                    <TableCell align="right">Score</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.top_opportunities.map((r) => (
                    <TableRow key={r.hcp_id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{r.hcp_name}</TableCell>
                      <TableCell>{r.specialty_group}</TableCell>
                      <TableCell>{r.territory}</TableCell>
                      <TableCell align="right">
                        <Chip
                          size="small"
                          label={r.opportunity_score?.toFixed(0)}
                          sx={{ bgcolor: palette.primary, color: "#fff", fontWeight: 700 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Recent Market Events</Typography>
              <Stack spacing={1.2}>
                {data.recent_market_events.map((e) => (
                  <Paper key={e.market_event_id} variant="outlined" sx={{ p: 1.5, borderColor: palette.border }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" sx={{ fontWeight: 700 }}>{e.event_type}</Typography>
                      <Chip
                        size="small"
                        label={e.event_severity}
                        color={e.event_severity === "High" ? "error" : e.event_severity === "Medium" ? "warning" : "default"}
                      />
                    </Stack>
                    <Typography variant="caption" sx={{ color: palette.textMuted }}>
                      {e.event_date?.slice(0, 10)} · {e.region} · {e.source_name}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.5 }}>{e.summary_raw}</Typography>
                  </Paper>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
