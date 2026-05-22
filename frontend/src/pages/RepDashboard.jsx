import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, Grid, Typography, Stack, Chip, Avatar,
  Table, TableHead, TableRow, TableCell, TableBody, MenuItem, Select, FormControl, InputLabel,
} from "@mui/material";
import { RepApi, Conversion } from "../services/api";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from "recharts";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import { palette, chartPalette } from "../theme/kiwiTheme";
import KPICard from "../components/KPICard";

export default function RepDashboard() {
  const [reps, setReps] = useState([]);
  const [repId, setRepId] = useState("");
  const [detail, setDetail] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    RepApi.list().then((rs) => {
      setReps(rs);
      if (rs.length) setRepId(rs[0].rep_id);
    });
    RepApi.leaderboard().then(setLeaderboard);
  }, []);

  useEffect(() => {
    if (repId) RepApi.detail(repId).then(setDetail);
  }, [repId]);

  if (!reps.length) return <LoadingState />;
  return (
    <Box>
      <SectionHeader
        eyebrow="Field Effectiveness"
        title="Rep Coaching Dashboard"
        subtitle="Per-rep performance, quota attainment, and top accounts."
        actions={
          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>Rep</InputLabel>
            <Select
              data-testid="rep-select"
              label="Rep"
              value={repId}
              onChange={(e) => setRepId(e.target.value)}
            >
              {reps.map((r) => (
                <MenuItem key={r.rep_id} value={r.rep_id}>
                  {r.rep_name} · {r.territory}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        }
      />

      {!detail ? <LoadingState /> : (
        <Grid container spacing={2.5}>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                  <Avatar sx={{ width: 56, height: 56, bgcolor: palette.primary, fontFamily: "Sora", fontWeight: 700 }}>
                    {detail.rep.rep_name?.[0]}
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontFamily: "Sora" }}>{detail.rep.rep_name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {detail.rep.region} · {detail.rep.territory} · {detail.rep.primary_therapy_area}
                    </Typography>
                  </Box>
                </Stack>
                <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
                  <Chip label={`${detail.rep.seniority_level}`} size="small" />
                  <Chip label={`Quota ${detail.rep.quota_band}`} size="small" />
                  <Chip label={`Digital ${detail.rep.digital_adoption_tier}`} size="small" />
                  <Chip label={detail.rep.current_status} size="small" color="success" />
                </Stack>
                <Grid container spacing={1.2}>
                  <Grid item xs={6}><KPICard label="Calls" value={detail.performance.total_calls} accent={palette.primary} /></Grid>
                  <Grid item xs={6}>
                    <KPICard
                      label="Conversion"
                      value={detail.performance.conversion_rate}
                      unit="%"
                      accent={palette.accent}
                      sublabel={`${detail.performance.converted_calls} converted`}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Monthly Quota vs Target</Typography>
                <Box sx={{ height: 260 }}>
                  <ResponsiveContainer>
                    <BarChart data={detail.quota}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                      <XAxis dataKey="report_month" tickFormatter={(v) => v?.slice(0, 7)} tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="call_quota" fill={palette.primary} name="Call quota" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="target_hcp_visits" fill={palette.light} name="Target HCP visits" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Top HCPs</Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>HCP</TableCell>
                      <TableCell>Specialty</TableCell>
                      <TableCell>Territory</TableCell>
                      <TableCell align="right">Calls</TableCell>
                      <TableCell align="right">Converted</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {detail.top_hcps.map((r) => (
                      <TableRow key={r.hcp_id} hover>
                        <TableCell sx={{ fontWeight: 600 }}>{r.hcp_name}</TableCell>
                        <TableCell>{r.specialty_group}</TableCell>
                        <TableCell>{r.territory}</TableCell>
                        <TableCell align="right">{r.calls}</TableCell>
                        <TableCell align="right">
                          <Chip size="small" label={r.converted} sx={{ bgcolor: palette.cream, color: palette.primaryDark, fontWeight: 700 }} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Field Leaderboard</Typography>
                <Stack spacing={1}>
                  {leaderboard.slice(0, 10).map((r, i) => (
                    <Box
                      key={r.rep_name}
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        p: 1.2,
                        borderRadius: 2,
                        bgcolor: r.rep_name === detail.rep.rep_name ? "rgba(146,222,139,0.25)" : palette.surfaceAlt,
                      }}
                    >
                      <Stack direction="row" spacing={1.2} alignItems="center">
                        <Box sx={{
                          width: 22, height: 22, borderRadius: "50%",
                          bgcolor: i < 3 ? palette.primary : palette.border,
                          color: i < 3 ? "#fff" : palette.text,
                          display: "grid", placeItems: "center", fontSize: 11, fontWeight: 700,
                        }}>
                          {i + 1}
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>{r.rep_name}</Typography>
                      </Stack>
                      <Chip size="small" label={`${r.conversion_rate?.toFixed(0)}%`} sx={{ bgcolor: palette.surface, fontWeight: 700 }} />
                    </Box>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
