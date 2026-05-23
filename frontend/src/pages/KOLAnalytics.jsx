import React, { useEffect, useState, useRef, useMemo } from "react";
import {
  Box, Card, CardContent, Grid, Typography, Stack, Chip,
  Table, TableHead, TableRow, TableCell, TableBody,
} from "@mui/material";
import ForceGraph2D from "react-force-graph-2d";
import { KOL } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import KPICard from "../components/KPICard";
import LoadingState from "../components/LoadingState";
import { palette, chartPalette } from "../theme/kiwiTheme";
import FilterBar, { buildFilterParams, EMPTY_FILTERS } from "../components/FilterBar";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";

export default function KOLAnalytics() {
  const [dash, setDash] = useState(null);
  const [topics, setTopics] = useState([]);
  const [network, setNetwork] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const containerRef = useRef(null);
  const [size, setSize] = useState({ w: 600, h: 480 });

  useEffect(() => {
    const p = buildFilterParams(filters);
    // KOL doesn't use territory/time_window; drop them for the API
    delete p.territory;
    delete p.time_window_days;
    setDash(null);
    KOL.dashboard(p).then(setDash);
    KOL.topics(p).then(setTopics);
    KOL.network(null, p).then(setNetwork);
  }, [filters]);

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setSize({ w: containerRef.current.clientWidth - 24, h: 480 });
      }
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  const graphData = useMemo(() => {
    if (!network) return { nodes: [], links: [] };
    return {
      nodes: network.nodes.map((n) => ({
        id: n.id, label: n.label, val: 1 + n.influence * 6, color: tierColor(n.tier),
      })),
      links: network.edges.map((e) => ({
        source: e.source, target: e.target, value: e.weight,
      })),
    };
  }, [network]);

  if (!dash) return (
    <Box>
      <SectionHeader
        eyebrow="Scientific Influence"
        title="KOL Analytics & Network"
        subtitle="Co-author networks, topic momentum, and rising-star KOLs feeding rep briefings and HCP targeting."
      />
      <FilterBar value={filters} onChange={setFilters} testidPrefix="kol-filter"
        show={{ specialty: true, territory: false, region: true, time_window_days: false }} />
      <LoadingState label="Loading KOL analytics…" />
    </Box>
  );
  const s = dash.summary;

  return (
    <Box>
      <SectionHeader
        eyebrow="Scientific Influence"
        title="KOL Analytics & Network"
        subtitle="Co-author networks, topic momentum, and rising-star KOLs feeding rep briefings and HCP targeting."
      />

      <FilterBar value={filters} onChange={setFilters} testidPrefix="kol-filter"
        show={{ specialty: true, territory: false, region: true, time_window_days: false }} />

      <Grid container spacing={2.5} sx={{ mb: 2 }}>
        <Grid item xs={6} md={3}><KPICard label="Total KOLs" value={s.total_kols} accent={palette.primary} /></Grid>
        <Grid item xs={6} md={3}><KPICard label="Tier 1" value={s.tier1} accent={palette.accent} /></Grid>
        <Grid item xs={6} md={3}><KPICard label="Rising stars" value={s.rising_stars} accent={palette.light} /></Grid>
        <Grid item xs={6} md={3}><KPICard label="Avg influence" value={(s.avg_influence * 100).toFixed(0)} unit="/100" accent={palette.cream} /></Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid item xs={12} lg={8}>
          <Card ref={containerRef} data-testid="kol-network-card">
            <CardContent>
              <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Co-author Network</Typography>
                <Stack direction="row" spacing={1}>
                  <LegendDot color={tierColor("Tier 1")} label="Tier 1" />
                  <LegendDot color={tierColor("Tier 2")} label="Tier 2" />
                  <LegendDot color={tierColor("Tier 3")} label="Tier 3" />
                </Stack>
              </Stack>
              <Box sx={{ height: 480, borderRadius: 2, bgcolor: "#FBFEFB", border: `1px solid ${palette.border}`, position: "relative", overflow: "hidden" }}>
                <ForceGraph2D
                  graphData={graphData}
                  width={size.w}
                  height={480}
                  nodeLabel={(n) => `${n.label}`}
                  linkColor={() => "rgba(2,129,116,0.25)"}
                  linkWidth={(l) => (l.value || 0.4) * 2}
                  nodeCanvasObject={(node, ctx, scale) => {
                    const r = node.val;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                    ctx.fillStyle = node.color;
                    ctx.fill();
                    if (scale > 1.5) {
                      ctx.fillStyle = palette.primaryDark;
                      ctx.font = `${10 / scale * 1.4}px DM Sans`;
                      ctx.fillText(node.label, node.x + r + 2, node.y + 3);
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Top KOLs</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Specialty</TableCell>
                    <TableCell align="right">Influence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dash.top.slice(0, 10).map((k) => (
                    <TableRow key={k.kol_id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{k.hcp_name}</TableCell>
                      <TableCell>
                        <Stack direction="column" spacing={0.2}>
                          <Typography variant="caption">{k.specialty_group}</Typography>
                          <Chip size="small" label={k.kol_tier} sx={{ bgcolor: tierColor(k.kol_tier), color: "#fff", fontSize: 10, height: 18 }}/>
                        </Stack>
                      </TableCell>
                      <TableCell align="right">{(k.influence_score * 100).toFixed(0)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Topic Momentum</Typography>
              <Box sx={{ height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={topics}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                    <XAxis dataKey="topic" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="kols" name="KOLs" radius={[8, 8, 0, 0]}>
                      {topics.map((_, i) => <Cell key={i} fill={chartPalette[i % chartPalette.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

function tierColor(t) {
  if (t === "Tier 1") return palette.primary;
  if (t === "Tier 2") return palette.accent;
  return palette.light;
}

function LegendDot({ color, label }) {
  return (
    <Stack direction="row" spacing={0.6} alignItems="center">
      <Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: color }} />
      <Typography variant="caption">{label}</Typography>
    </Stack>
  );
}
