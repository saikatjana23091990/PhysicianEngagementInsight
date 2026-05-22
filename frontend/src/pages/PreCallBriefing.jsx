import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box, Card, CardContent, Grid, Typography, Stack, Chip, Button, MenuItem, Select, FormControl, InputLabel,
  LinearProgress, Divider, Paper, Avatar,
} from "@mui/material";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import VerifiedRoundedIcon from "@mui/icons-material/VerifiedRounded";
import ReactMarkdown from "react-markdown";
import { HCPApi, Briefing } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import { palette } from "../theme/kiwiTheme";

export default function PreCallBriefing() {
  const { hcpId } = useParams();
  const navigate = useNavigate();
  const [hcps, setHcps] = useState([]);
  const [selected, setSelected] = useState(hcpId || "");
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { HCPApi.list({ limit: 50 }).then((d) => setHcps(d.items)); }, []);
  useEffect(() => { if (hcpId) setSelected(hcpId); }, [hcpId]);

  const generate = async () => {
    if (!selected) return;
    setLoading(true);
    setBrief(null);
    try {
      const b = await Briefing.generate(selected);
      setBrief(b);
    } catch (e) {
      setBrief({ brief_markdown: "Generation failed: " + (e.response?.data?.detail || e.message) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <SectionHeader
        eyebrow="Rep Copilot"
        title="Pre-Call Briefing Assistant"
        subtitle="AI-generated, source-grounded briefing — built from claims, calls, notes, publications, events, KOL signals, and conversion history."
        actions={
          <Stack direction="row" spacing={1.5}>
            <FormControl size="small" sx={{ minWidth: 260 }}>
              <InputLabel>HCP</InputLabel>
              <Select
                data-testid="briefing-hcp-select"
                label="HCP"
                value={selected}
                onChange={(e) => { setSelected(e.target.value); navigate(`/briefing/${e.target.value}`); }}
              >
                {hcps.map((h) => (
                  <MenuItem key={h.hcp_id} value={h.hcp_id}>
                    {h.hcp_name} · {h.specialty_group}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              data-testid="generate-brief-btn"
              variant="contained"
              startIcon={<AutoAwesomeRoundedIcon />}
              onClick={generate}
              disabled={!selected || loading}
            >
              {loading ? "Generating…" : "Generate Brief"}
            </Button>
          </Stack>
        }
      />

      {loading && <LinearProgress sx={{ mb: 2, borderRadius: 2 }} />}

      <Grid container spacing={2.5}>
        <Grid item xs={12} lg={8}>
          <Card data-testid="brief-output-card" sx={{ minHeight: 400 }}>
            <CardContent>
              {!brief && !loading && (
                <Box sx={{ textAlign: "center", py: 6 }}>
                  <Avatar sx={{ width: 56, height: 56, bgcolor: "rgba(10,182,139,0.12)", color: palette.accent, mx: "auto", mb: 2 }}>
                    <AutoAwesomeRoundedIcon />
                  </Avatar>
                  <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Select an HCP and generate</Typography>
                  <Typography variant="body2" sx={{ color: palette.textMuted }}>
                    Briefs are grounded in the source records (calls, claims, pubs, events) for full traceability.
                  </Typography>
                </Box>
              )}
              {brief && (
                <Box>
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
                    <Box>
                      <Typography variant="overline" sx={{ color: palette.textMuted }}>
                        Pre-Call Brief
                      </Typography>
                      <Typography variant="h5" sx={{ fontFamily: "Sora" }}>{brief.hcp_name}</Typography>
                      <Typography variant="caption" sx={{ color: palette.textMuted }}>
                        {brief.specialty} · {brief.region} · {brief.territory} · Consent: {brief.consent}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={0.8}>
                      <Chip size="small" icon={<VerifiedRoundedIcon />} label={`${brief.provider}`} sx={{ bgcolor: palette.cream, color: palette.primaryDark, fontWeight: 600 }} />
                      <Chip size="small" label={`${brief.latency_ms} ms`} sx={{ bgcolor: palette.surfaceAlt }} />
                      {brief.fallback_used && <Chip size="small" label="fallback" color="warning" />}
                    </Stack>
                  </Stack>
                  <Divider sx={{ mb: 2 }} />
                  <Box sx={{
                    "& h2": { fontFamily: "Sora", fontSize: 18, mt: 2.5, mb: 1, color: palette.primaryDark },
                    "& h3": { fontFamily: "Sora", fontSize: 15, mt: 2, mb: 0.5 },
                    "& ul, & ol": { pl: 3, mb: 1 },
                    "& li": { mb: 0.5 },
                    "& p": { lineHeight: 1.65 },
                    "& code": { bgcolor: palette.cream, px: 0.5, py: 0.1, borderRadius: 0.5, fontFamily: "JetBrains Mono", fontSize: 12 },
                  }}>
                    <ReactMarkdown>{brief.brief_markdown}</ReactMarkdown>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Stack spacing={2}>
            {brief?.nba && (
              <Card data-testid="brief-nba-card">
                <CardContent>
                  <Typography variant="overline" sx={{ color: palette.textMuted }}>Next Best Action</Typography>
                  <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>{brief.nba.recommendation.action}</Typography>
                  <Chip size="small" label={brief.nba.recommendation.priority}
                    color={brief.nba.recommendation.priority === "High" ? "error" :
                      brief.nba.recommendation.priority === "Medium" ? "warning" : "default"}/>
                  <Typography variant="body2" sx={{ mt: 1.5, color: palette.text }}>
                    {brief.nba.recommendation.rationale}
                  </Typography>
                  <Divider sx={{ my: 1.5 }} />
                  <Typography variant="overline" sx={{ color: palette.textMuted }}>Top Drivers</Typography>
                  <Stack spacing={0.8} sx={{ mt: 0.5 }}>
                    {brief.nba.drivers.map(([name, v]) => (
                      <Box key={name}>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="caption">{name}</Typography>
                          <Typography variant="caption" sx={{ fontWeight: 700 }}>{Number(v).toFixed(0)}</Typography>
                        </Stack>
                        <LinearProgress variant="determinate" value={Number(v)} sx={{
                          height: 6, borderRadius: 3, bgcolor: palette.border,
                          "& .MuiLinearProgress-bar": { bgcolor: palette.accent },
                        }}/>
                      </Box>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            )}

            {brief?.retrieved_sources && (
              <Card data-testid="brief-sources-card">
                <CardContent>
                  <Typography variant="overline" sx={{ color: palette.textMuted }}>Retrieved Sources (RAG)</Typography>
                  <Typography variant="caption" sx={{ display: "block", color: palette.textMuted, mb: 1 }}>
                    Top {brief.retrieved_sources.length} records used for grounding.
                  </Typography>
                  <Stack spacing={1}>
                    {brief.retrieved_sources.slice(0, 8).map((s) => (
                      <Paper key={s.source_id} variant="outlined" sx={{ p: 1.2, borderColor: palette.border }}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.3 }}>
                          <Chip size="small" label={s.source_type} sx={{ bgcolor: palette.surfaceAlt, fontFamily: "JetBrains Mono", fontSize: 10 }} />
                          <Typography variant="caption" sx={{ color: palette.textMuted }}>{s.date}</Typography>
                        </Stack>
                        <Typography variant="caption" sx={{ fontFamily: "JetBrains Mono", color: palette.primary }}>{s.source_id}</Typography>
                        <Typography variant="body2" sx={{ display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden", mt: 0.3 }}>
                          {s.text}
                        </Typography>
                      </Paper>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            )}

            {brief?.compliance_audit && (
              <Card>
                <CardContent>
                  <Typography variant="overline" sx={{ color: palette.textMuted }}>Compliance Audit</Typography>
                  <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                    <Typography variant="caption">Records in context: {brief.compliance_audit.context_record_count}</Typography>
                    <Typography variant="caption">Retrieved: {brief.compliance_audit.retrieved_count}</Typography>
                    <Typography variant="caption">Prompt: {brief.compliance_audit.system_prompt_version}</Typography>
                  </Stack>
                </CardContent>
              </Card>
            )}
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
}
