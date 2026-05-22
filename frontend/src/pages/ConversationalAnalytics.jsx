import React, { useEffect, useRef, useState } from "react";
import {
  Box, Card, CardContent, Stack, TextField, IconButton, Typography, Chip, Avatar, Paper, Divider,
} from "@mui/material";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import ReactMarkdown from "react-markdown";
import { Chat } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import { palette } from "../theme/kiwiTheme";

export default function ConversationalAnalytics() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [suggested, setSuggested] = useState([]);
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);
  const sessionId = useRef(`s-${Date.now()}`);

  useEffect(() => { Chat.suggested().then(setSuggested); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await Chat.ask(q, messages.slice(-6), sessionId.current);
      setMessages((m) => [...m, {
        role: "assistant",
        content: res.answer_markdown,
        meta: {
          provider: res.provider,
          latency: res.latency_ms,
          sources: res.retrieved_sources,
          fallback: res.fallback_used,
        },
      }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <SectionHeader
        eyebrow="GenAI · AWS Bedrock"
        title="Ask Data — Conversational Analytics"
        subtitle="Ask anything about the commercial business. Answers are grounded in source records, cite sources, and surface caveats."
      />
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 320px" }, gap: 2.5 }}>
        <Card data-testid="chat-panel" sx={{ minHeight: 520, display: "flex", flexDirection: "column" }}>
          <CardContent sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <Box sx={{ flex: 1, overflowY: "auto", pr: 1, mb: 1 }}>
              {messages.length === 0 && (
                <Box sx={{ textAlign: "center", py: 6 }}>
                  <Avatar sx={{ width: 56, height: 56, bgcolor: "rgba(10,182,139,0.12)", color: palette.accent, mx: "auto", mb: 2 }}>
                    <AutoAwesomeRoundedIcon />
                  </Avatar>
                  <Typography variant="h6" sx={{ fontFamily: "Sora" }}>Start a conversation</Typography>
                  <Typography variant="body2" sx={{ color: palette.textMuted }}>
                    Try one of the suggested questions or type your own.
                  </Typography>
                </Box>
              )}
              {messages.map((m, i) => (
                <Box key={i} sx={{ display: "flex", mb: 2, justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 1.5, maxWidth: "80%",
                      bgcolor: m.role === "user" ? palette.primary : palette.surface,
                      color: m.role === "user" ? "#fff" : palette.text,
                      border: m.role === "user" ? "none" : `1px solid ${palette.border}`,
                      borderRadius: 2.5,
                      "& p": { mt: 0, mb: 0.8 },
                      "& h2": { fontFamily: "Sora", fontSize: 15, mt: 1.5, mb: 0.5 },
                      "& ul, & ol": { pl: 2.5 },
                    }}
                    data-testid={`chat-msg-${i}`}
                  >
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                    {m.meta && (
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 1 }}>
                        <Chip size="small" label={m.meta.provider} sx={{ bgcolor: palette.surfaceAlt, fontSize: 10 }} />
                        <Chip size="small" label={`${m.meta.latency} ms`} sx={{ bgcolor: palette.surfaceAlt, fontSize: 10 }} />
                        {m.meta.fallback && <Chip size="small" label="fallback" color="warning" sx={{ fontSize: 10 }} />}
                        {m.meta.sources?.length > 0 && (
                          <Chip size="small" label={`${m.meta.sources.length} sources`} sx={{ bgcolor: palette.cream, color: palette.primaryDark, fontSize: 10, fontWeight: 700 }} />
                        )}
                      </Stack>
                    )}
                  </Paper>
                </Box>
              ))}
              {loading && (
                <Box sx={{ display: "flex", justifyContent: "flex-start", mb: 2 }}>
                  <Paper sx={{ p: 1.5, bgcolor: palette.surfaceAlt }}>
                    <Typography variant="body2" sx={{ color: palette.textMuted }}>
                      <span className="dot-pulse">●</span> thinking…
                    </Typography>
                  </Paper>
                </Box>
              )}
              <div ref={endRef} />
            </Box>
            <Divider sx={{ my: 1 }} />
            <Stack direction="row" spacing={1} alignItems="center">
              <TextField
                fullWidth
                size="small"
                placeholder="Ask about conversion, KOLs, reps, territory…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                data-testid="chat-input"
                disabled={loading}
              />
              <IconButton color="primary" onClick={() => send()} disabled={loading || !input.trim()} data-testid="chat-send">
                <SendRoundedIcon />
              </IconButton>
            </Stack>
          </CardContent>
        </Card>

        <Stack spacing={2}>
          <Card>
            <CardContent>
              <Typography variant="overline" sx={{ color: palette.textMuted }}>Suggested questions</Typography>
              <Stack spacing={1} sx={{ mt: 1 }}>
                {suggested.map((q, i) => (
                  <Chip
                    key={i}
                    label={q}
                    onClick={() => send(q)}
                    data-testid={`suggested-${i}`}
                    sx={{
                      height: "auto",
                      py: 1,
                      px: 1.2,
                      bgcolor: palette.surfaceAlt,
                      color: palette.text,
                      whiteSpace: "normal",
                      "& .MuiChip-label": { display: "block", textAlign: "left", whiteSpace: "normal", fontSize: 12.5, lineHeight: 1.4 },
                      cursor: "pointer",
                      "&:hover": { bgcolor: palette.cream },
                    }}
                  />
                ))}
              </Stack>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="overline" sx={{ color: palette.textMuted }}>Guardrails</Typography>
              <Stack spacing={0.8} sx={{ mt: 1 }}>
                <ChipRow label="Source grounded" />
                <ChipRow label="Citation enforced" />
                <ChipRow label="No off-label claims" />
                <ChipRow label="Audit logged" />
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Box>
    </Box>
  );
}

function ChipRow({ label }) {
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Box sx={{ width: 6, height: 6, borderRadius: "50%", bgcolor: palette.accent }} />
      <Typography variant="caption">{label}</Typography>
    </Stack>
  );
}
