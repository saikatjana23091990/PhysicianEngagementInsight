import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Box, Grid, Card, CardContent, Typography, Stack, Chip, Avatar, Button, Divider,
  Tabs, Tab, Table, TableHead, TableRow, TableCell, TableBody, LinearProgress, Paper,
} from "@mui/material";
import EventAvailableRoundedIcon from "@mui/icons-material/EventAvailableRounded";
import BoltRoundedIcon from "@mui/icons-material/BoltRounded";
import { HCPApi } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import KPICard from "../components/KPICard";
import { palette } from "../theme/kiwiTheme";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from "recharts";

export default function HCPDetail() {
  const { hcpId } = useParams();
  const [data, setData] = useState(null);
  const [opp, setOpp] = useState(null);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    HCPApi.detail(hcpId).then(setData);
    HCPApi.opportunity(hcpId).then(setOpp);
  }, [hcpId]);

  if (!data) return <LoadingState />;
  const h = data.hcp;
  const rxTrend = [...data.claims].reverse().map((c) => ({
    month: c.service_month?.slice(0, 7),
    n_rx: c.n_rx,
    new_rx: c.new_rx,
  }));

  const radar = opp?.drivers
    ? opp.drivers.map(([k, v]) => ({ driver: k, value: Number(v) }))
    : [];

  return (
    <Box>
      <SectionHeader
        eyebrow={h.hcp_id}
        title={h.hcp_name}
        subtitle={`${h.specialty_group} · ${h.sub_specialty} · ${h.affiliated_hospital}`}
        actions={
          <Stack direction="row" spacing={1}>
            <Button
              data-testid="brief-cta"
              component={Link}
              to={`/briefing/${hcpId}`}
              variant="contained"
              startIcon={<EventAvailableRoundedIcon />}
            >
              Generate Pre-Call Brief
            </Button>
          </Stack>
        }
      />

      <Grid container spacing={2.5}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Stack direction="row" spacing={2} flexWrap="wrap">
                <Chip label={`Region: ${h.region}`} />
                <Chip label={`Territory: ${h.territory}`} />
                <Chip label={`Channel: ${h.channel_preference}`} />
                <Chip
                  label={`Consent: ${h.consent_status}`}
                  color={h.consent_status === "Opted-in" ? "success" : h.consent_status === "Opted-out" ? "error" : "default"}
                />
                <Chip label={`Digital: ${h.digital_engagement_tier}`} sx={{ bgcolor: palette.surfaceAlt }} />
                <Chip label={`Publications: ${h.publication_activity_level}`} sx={{ bgcolor: palette.cream, color: palette.primaryDark }} />
              </Stack>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Prescription Trend</Typography>
              <Box sx={{ height: 220 }}>
                <ResponsiveContainer>
                  <AreaChart data={rxTrend}>
                    <defs>
                      <linearGradient id="rx" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={palette.primary} stopOpacity={0.4} />
                        <stop offset="100%" stopColor={palette.primary} stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="n_rx" stroke={palette.primary} fill="url(#rx)" strokeWidth={2.5} />
                    <Area type="monotone" dataKey="new_rx" stroke={palette.accent} fill="none" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: "100%" }} data-testid="opportunity-card">
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Typography variant="overline" sx={{ color: palette.textMuted }}>Opportunity Score</Typography>
                <BoltRoundedIcon sx={{ color: palette.accent }} />
              </Stack>
              <Typography variant="h2" sx={{ fontFamily: "Sora", color: palette.primary, lineHeight: 1, my: 0.5 }}>
                {opp?.opportunity_score?.toFixed(0) || "—"}
              </Typography>
              <Typography variant="caption" sx={{ color: palette.textMuted }}>
                Confidence {(opp?.confidence * 100)?.toFixed(0)}%
              </Typography>
              {opp?.recommendation && (
                <Paper variant="outlined" sx={{ p: 1.5, mt: 2, borderColor: palette.border }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                    <Typography variant="body2" sx={{ fontWeight: 700 }}>{opp.recommendation.action}</Typography>
                    <Chip size="small" label={opp.recommendation.priority} color={
                      opp.recommendation.priority === "High" ? "error" : opp.recommendation.priority === "Medium" ? "warning" : "default"
                    }/>
                  </Stack>
                  <Typography variant="caption" sx={{ color: palette.textMuted }}>{opp.recommendation.rationale}</Typography>
                </Paper>
              )}
              <Box sx={{ height: 220, mt: 1 }}>
                <ResponsiveContainer>
                  <RadarChart data={radar}>
                    <PolarGrid stroke="#E4ECE6" />
                    <PolarAngleAxis dataKey="driver" tick={{ fontSize: 10 }} />
                    <PolarRadiusAxis tick={{ fontSize: 10 }} angle={90} domain={[0, 100]} />
                    <Radar dataKey="value" stroke={palette.primary} fill={palette.accent} fillOpacity={0.45} />
                  </RadarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 1.5 }}>
                <Tab label={`Calls (${data.calls.length})`} data-testid="tab-calls" />
                <Tab label={`Publications (${data.publications.length})`} data-testid="tab-publications" />
                <Tab label={`Events (${data.events.length})`} data-testid="tab-events" />
                <Tab label={`Digital (${data.digital_engagement.length})`} data-testid="tab-digital" />
              </Tabs>
              {tab === 0 && (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Rep</TableCell>
                      <TableCell>Channel</TableCell>
                      <TableCell>Topic</TableCell>
                      <TableCell>Outcome</TableCell>
                      <TableCell>Note</TableCell>
                      <TableCell>Converted</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.calls.map((c) => (
                      <TableRow key={c.interaction_id} hover>
                        <TableCell>{c.interaction_datetime?.slice(0, 10)}</TableCell>
                        <TableCell>{c.rep_id}</TableCell>
                        <TableCell>{c.channel}</TableCell>
                        <TableCell>{c.discussion_topic}</TableCell>
                        <TableCell>{c.call_outcome}</TableCell>
                        <TableCell sx={{ maxWidth: 320 }}>
                          <Typography variant="caption" sx={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                            {c.crm_note_raw}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {c.converted ? (
                            <Chip size="small" label={c.conversion_type || "Yes"} sx={{ bgcolor: palette.primary, color: "#fff" }} />
                          ) : (
                            <Chip size="small" label="No" sx={{ bgcolor: palette.surfaceAlt }} />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {tab === 1 && (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Title</TableCell>
                      <TableCell>Journal</TableCell>
                      <TableCell>Topic</TableCell>
                      <TableCell>Sentiment</TableCell>
                      <TableCell align="right">Relevance</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.publications.map((p) => (
                      <TableRow key={p.publication_id} hover>
                        <TableCell>{p.publication_date?.slice(0, 10)}</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{p.publication_title}</TableCell>
                        <TableCell>{p.journal_name}</TableCell>
                        <TableCell>{p.topic_tag}</TableCell>
                        <TableCell>
                          <Chip size="small" label={p.topic_sentiment}
                            color={p.topic_sentiment === "Positive" ? "success" : p.topic_sentiment === "Negative" ? "error" : "default"} />
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ width: 80, ml: "auto" }}>
                            <LinearProgress variant="determinate" value={(p.relevance_score || 0) * 100}
                              sx={{ height: 8, borderRadius: 4, bgcolor: palette.border, "& .MuiLinearProgress-bar": { bgcolor: palette.primary } }}/>
                            <Typography variant="caption">{p.relevance_score?.toFixed(2)}</Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {tab === 2 && (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Event</TableCell>
                      <TableCell>Topic</TableCell>
                      <TableCell>Source</TableCell>
                      <TableCell align="right">Engagement</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.events.map((e) => (
                      <TableRow key={e.event_id} hover>
                        <TableCell>{e.event_date?.slice(0, 10)}</TableCell>
                        <TableCell>{e.event_type}</TableCell>
                        <TableCell>{e.topic}</TableCell>
                        <TableCell>{e.source}</TableCell>
                        <TableCell align="right">{e.engagement_score?.toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {tab === 3 && (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Touchpoint</TableCell>
                      <TableCell>Event</TableCell>
                      <TableCell>Device</TableCell>
                      <TableCell align="right">Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.digital_engagement.map((d) => (
                      <TableRow key={d.engagement_id} hover>
                        <TableCell>{d.engagement_date?.slice(0, 10)}</TableCell>
                        <TableCell>{d.touchpoint}</TableCell>
                        <TableCell>{d.engagement_event}</TableCell>
                        <TableCell>{d.device_type}</TableCell>
                        <TableCell align="right">{d.engagement_value}</TableCell>
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
