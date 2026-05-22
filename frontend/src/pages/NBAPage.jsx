import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, Grid, Typography, Stack, Chip, MenuItem, Select, FormControl, InputLabel,
  Table, TableHead, TableRow, TableCell, TableBody, LinearProgress, Button, Drawer, Divider, Avatar,
} from "@mui/material";
import { NBA, HCPApi } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import { palette } from "../theme/kiwiTheme";
import { Link } from "react-router-dom";

export default function NBAPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [specialty, setSpecialty] = useState("");
  const [specs, setSpecs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [sim, setSim] = useState(null);

  useEffect(() => { HCPApi.specialties().then(setSpecs); }, []);

  useEffect(() => {
    setLoading(true);
    NBA.ranked({ specialty: specialty || undefined, limit: 50 }).then(setItems).finally(() => setLoading(false));
  }, [specialty]);

  const openDetail = async (hcp_id) => {
    const det = await NBA.explain(hcp_id);
    setSelected(det);
    setSim(null);
  };

  const runScenario = async (scenario) => {
    if (!selected) return;
    const r = await NBA.simulate(selected.hcp_id, scenario);
    setSim(r);
  };

  return (
    <Box>
      <SectionHeader
        eyebrow="Targeting Copilot"
        title="HCP Targeting & Next-Best-Action"
        subtitle="Opportunity-ranked HCP list with explainable score drivers, rule-based NBA, and scenario simulation."
        actions={
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Specialty</InputLabel>
            <Select
              data-testid="nba-specialty-filter"
              label="Specialty"
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
            >
              <MenuItem value=""><em>All</em></MenuItem>
              {specs.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
            </Select>
          </FormControl>
        }
      />

      <Card>
        <CardContent sx={{ p: 0 }}>
          {loading ? <LoadingState /> : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>HCP</TableCell>
                  <TableCell>Specialty</TableCell>
                  <TableCell>Territory</TableCell>
                  <TableCell>Consent</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell>Drivers</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell align="right"></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((r, i) => (
                  <TableRow key={r.hcp_id} hover sx={{ cursor: "pointer" }} onClick={() => openDetail(r.hcp_id)} data-testid={`nba-row-${r.hcp_id}`}>
                    <TableCell>
                      <Stack direction="row" spacing={1.2} alignItems="center">
                        <Box sx={{
                          width: 28, height: 28, borderRadius: "50%",
                          bgcolor: i < 5 ? palette.primary : palette.surfaceAlt,
                          color: i < 5 ? "#fff" : palette.text,
                          display: "grid", placeItems: "center", fontWeight: 700, fontSize: 12,
                        }}>{i + 1}</Box>
                        <Box>
                          <Box sx={{ fontWeight: 700 }}>{r.hcp_name}</Box>
                          <Box sx={{ fontSize: 11, color: palette.textMuted }}>{r.affiliated_hospital}</Box>
                        </Box>
                      </Stack>
                    </TableCell>
                    <TableCell>{r.specialty_group}</TableCell>
                    <TableCell>{r.territory}</TableCell>
                    <TableCell>
                      <Chip size="small" label={r.consent_status}
                        color={r.consent_status === "Opted-in" ? "success" : r.consent_status === "Opted-out" ? "error" : "default"}/>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Box sx={{ width: 80 }}>
                          <LinearProgress variant="determinate" value={r.opportunity_score} sx={{
                            height: 8, borderRadius: 4, bgcolor: palette.border,
                            "& .MuiLinearProgress-bar": { bgcolor: palette.accent },
                          }}/>
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>{r.opportunity_score?.toFixed(0)}</Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={0.5}>
                        <DriverDot label="G" v={r.drv_growth} />
                        <DriverDot label="E" v={r.drv_engagement} />
                        <DriverDot label="P" v={r.drv_publications} />
                        <DriverDot label="K" v={r.drv_kol} />
                        <DriverDot label="H" v={r.drv_history} />
                        <DriverDot label="U" v={r.drv_urgency} />
                      </Stack>
                    </TableCell>
                    <TableCell>{(r.score_confidence * 100).toFixed(0)}%</TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined" component={Link} to={`/briefing/${r.hcp_id}`} data-testid={`brief-${r.hcp_id}`}>Brief</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Drawer anchor="right" open={!!selected} onClose={() => setSelected(null)}
        PaperProps={{ sx: { width: { xs: "100%", md: 440 }, p: 3, background: palette.bg } }}>
        {selected && (
          <Box data-testid="nba-detail-drawer">
            <Typography variant="overline" sx={{ color: palette.textMuted }}>{selected.hcp_id}</Typography>
            <Typography variant="h4" sx={{ fontFamily: "Sora", mt: 0.5 }}>
              {items.find(i => i.hcp_id === selected.hcp_id)?.hcp_name}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip label={`Score ${selected.opportunity_score?.toFixed(0)}`} sx={{ bgcolor: palette.primary, color: "#fff" }}/>
              <Chip label={`Confidence ${(selected.confidence*100).toFixed(0)}%`} />
            </Stack>

            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="overline" sx={{ color: palette.textMuted }}>Recommendation</Typography>
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>{selected.recommendation.action}</Typography>
                <Chip size="small" label={selected.recommendation.priority}
                  color={selected.recommendation.priority === "High" ? "error" : selected.recommendation.priority === "Medium" ? "warning" : "default"} sx={{ mt: 0.5 }} />
                <Typography variant="body2" sx={{ mt: 1 }}>{selected.recommendation.rationale}</Typography>
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="caption" color="text.secondary">Channel: {selected.recommendation.channel}</Typography>
              </CardContent>
            </Card>

            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="overline" sx={{ color: palette.textMuted }}>Drivers (Top 5)</Typography>
                <Stack spacing={1} sx={{ mt: 1 }}>
                  {selected.drivers.map(([k, v]) => (
                    <Box key={k}>
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="caption">{k}</Typography>
                        <Typography variant="caption" sx={{ fontWeight: 700 }}>{Number(v).toFixed(0)}</Typography>
                      </Stack>
                      <LinearProgress variant="determinate" value={Number(v)} sx={{
                        height: 6, borderRadius: 3, bgcolor: palette.border,
                        "& .MuiLinearProgress-bar": { bgcolor: palette.accent }}}/>
                    </Box>
                  ))}
                </Stack>
                {selected.suppressors?.length > 0 && (
                  <>
                    <Divider sx={{ my: 1.5 }} />
                    <Typography variant="overline" sx={{ color: palette.textMuted }}>Suppressors</Typography>
                    {selected.suppressors.map((s, i) => (
                      <Chip key={i} size="small" label={`${s.factor} · ${s.impact}`} color="error" sx={{ mr: 0.5, mt: 0.5 }} />
                    ))}
                  </>
                )}
              </CardContent>
            </Card>

            <Card sx={{ mt: 2 }} data-testid="scenario-card">
              <CardContent>
                <Typography variant="overline" sx={{ color: palette.textMuted }}>Scenario Simulator</Typography>
                <Stack direction="row" spacing={0.8} flexWrap="wrap" sx={{ mt: 1, gap: 0.8 }}>
                  <Button size="small" variant="outlined" onClick={() => runScenario("competitor_event")}>Competitor event</Button>
                  <Button size="small" variant="outlined" onClick={() => runScenario("new_publication")}>New publication</Button>
                  <Button size="small" variant="outlined" onClick={() => runScenario("digital_boost")}>Digital boost</Button>
                  <Button size="small" variant="outlined" onClick={() => runScenario("rep_reassign")}>Rep reassign</Button>
                </Stack>
                {sim && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2"><b>Scenario:</b> {sim.scenario}</Typography>
                    <Typography variant="body2">Before score: {sim.before.opportunity_score?.toFixed(0)} → After: <b>{sim.after.opportunity_score.toFixed(0)}</b></Typography>
                    <Typography variant="body2">New action: <b>{sim.after.recommendation.action}</b></Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        )}
      </Drawer>
    </Box>
  );
}

function DriverDot({ label, v }) {
  const intensity = Math.min(1, (v || 0) / 100);
  const bg = `rgba(2, 129, 116, ${0.15 + intensity * 0.7})`;
  return (
    <Box sx={{
      width: 22, height: 22, borderRadius: "5px",
      bgcolor: bg, color: intensity > 0.5 ? "#fff" : palette.primaryDark,
      display: "grid", placeItems: "center", fontWeight: 700, fontSize: 10, fontFamily: "JetBrains Mono",
    }} title={`${label}: ${Number(v).toFixed(0)}`}>{label}</Box>
  );
}
