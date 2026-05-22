import React, { useEffect, useState } from "react";
import { Box, Card, CardContent, Grid, Typography, Chip, Stack, Divider, Paper, Avatar, Table, TableHead, TableRow, TableCell, TableBody } from "@mui/material";
import SecurityRoundedIcon from "@mui/icons-material/SecurityRounded";
import CloudRoundedIcon from "@mui/icons-material/CloudRounded";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import PsychologyRoundedIcon from "@mui/icons-material/PsychologyRounded";
import HistoryRoundedIcon from "@mui/icons-material/HistoryRounded";
import { api, Audit } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import { palette } from "../theme/kiwiTheme";

export default function AdminSettings() {
  const [health, setHealth] = useState(null);
  const [aiHistory, setAiHistory] = useState([]);
  useEffect(() => {
    api.get("/health").then((r) => setHealth(r.data));
    Audit.ai_outputs({ limit: 10 }).then((d) => setAiHistory(d.items || [])).catch(() => {});
  }, []);

  return (
    <Box>
      <SectionHeader
        eyebrow="Platform"
        title="Settings & Architecture"
        subtitle="Configuration, integrations, and data inventory. AWS deployment + Bedrock provider config managed via environment."
      />
      <Grid container spacing={2.5}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
                <Avatar sx={{ bgcolor: "rgba(2,129,116,0.12)", color: palette.primary }}><PsychologyRoundedIcon /></Avatar>
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>GenAI Provider</Typography>
              </Stack>
              <Stack spacing={1}>
                <Row k="LLM Provider" v="Emergent (primary) + AWS Bedrock (fallback-ready)" />
                <Row k="Bedrock model" v="anthropic.claude-3-5-sonnet-20241022-v2:0" />
                <Row k="Embedding model" v="amazon.titan-embed-text-v2:0" />
                <Row k="Vector store" v="Local TF-IDF (FAISS-ready)" />
                <Row k="Guardrails" v="v1.0 — source-grounded, citation-enforced, off-label blocked" />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
                <Avatar sx={{ bgcolor: "rgba(10,182,139,0.12)", color: palette.accent }}><StorageRoundedIcon /></Avatar>
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Data Inventory</Typography>
              </Stack>
              {health && (
                <Stack direction="row" flexWrap="wrap" gap={0.8} sx={{ mt: 1 }}>
                  {Object.entries(health.row_counts || {}).map(([k, v]) => (
                    <Chip key={k} size="small"
                      label={`${k} · ${v}`}
                      sx={{ bgcolor: palette.surfaceAlt, fontFamily: "JetBrains Mono", fontSize: 11 }} />
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
                <Avatar sx={{ bgcolor: "rgba(146,222,139,0.4)", color: palette.primaryDark }}><CloudRoundedIcon /></Avatar>
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>AWS Deployment</Typography>
              </Stack>
              <Stack spacing={1}>
                <Row k="Frontend" v="S3 + CloudFront" />
                <Row k="Backend" v="Lambda + Mangum (FastAPI) or ECS Fargate" />
                <Row k="Database" v="MongoDB Atlas (or DynamoDB)" />
                <Row k="Storage" v="S3 raw data lake" />
                <Row k="GenAI" v="Amazon Bedrock (Claude)" />
                <Row k="Secrets" v="AWS Secrets Manager / SSM" />
                <Row k="Observability" v="CloudWatch + X-Ray" />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
                <Avatar sx={{ bgcolor: "rgba(255,227,179,0.6)", color: palette.primaryDark }}><SecurityRoundedIcon /></Avatar>
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Compliance & Audit</Typography>
              </Stack>
              <Stack spacing={1}>
                <Row k="PHI masking" v="Enabled at UI layer" />
                <Row k="Source citation" v="Required on every AI response" />
                <Row k="Off-label filter" v="Active" />
                <Row k="Audit trail" v="Per-call attribution + AI response logging" />
                <Row k="Role-aware UI" v="Rep / Manager / Executive" />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card data-testid="ai-history-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
                <Avatar sx={{ bgcolor: "rgba(2,129,116,0.12)", color: palette.primary }}><HistoryRoundedIcon /></Avatar>
                <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Recent AI Outputs (Audit Trail)</Typography>
                <Chip size="small" label={`${aiHistory.length} logged`} sx={{ bgcolor: palette.cream, color: palette.primaryDark, fontWeight: 700 }} />
              </Stack>
              {aiHistory.length === 0 ? (
                <Typography variant="body2" sx={{ color: palette.textMuted }}>
                  No AI outputs persisted yet. Generate a briefing or chat to populate the audit log.
                </Typography>
              ) : (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>When</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>HCP / Question</TableCell>
                      <TableCell>Provider</TableCell>
                      <TableCell>Latency</TableCell>
                      <TableCell>Citations</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {aiHistory.map((r, i) => (
                      <TableRow key={i} hover>
                        <TableCell sx={{ fontFamily: "JetBrains Mono", fontSize: 11 }}>
                          {r.created_at?.slice(11, 19)}
                        </TableCell>
                        <TableCell>
                          <Chip size="small" label={r.type} sx={{ bgcolor: palette.surfaceAlt, fontFamily: "JetBrains Mono", fontSize: 10 }} />
                        </TableCell>
                        <TableCell sx={{ maxWidth: 380, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {r.hcp_id || r.question || "—"}
                        </TableCell>
                        <TableCell>{r.provider}</TableCell>
                        <TableCell>{r.latency_ms} ms</TableCell>
                        <TableCell>
                          <Stack direction="row" spacing={0.3} flexWrap="wrap" sx={{ maxWidth: 220 }}>
                            {(r.citations || []).slice(0, 4).map((c) => (
                              <Chip key={c} size="small" label={c} sx={{ bgcolor: palette.surfaceAlt, fontFamily: "JetBrains Mono", fontSize: 10, height: 18 }} />
                            ))}
                            {r.citations?.length > 4 && (
                              <Chip size="small" label={`+${r.citations.length - 4}`} sx={{ bgcolor: palette.surfaceAlt, fontSize: 10, height: 18 }} />
                            )}
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

function Row({ k, v }) {
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ py: 0.4 }}>
      <Typography variant="body2" sx={{ color: palette.textMuted }}>{k}</Typography>
      <Typography variant="body2" sx={{ fontWeight: 600, textAlign: "right", maxWidth: "60%" }}>{v}</Typography>
    </Stack>
  );
}
