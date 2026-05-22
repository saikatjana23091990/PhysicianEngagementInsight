import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, Stack, MenuItem, Select, FormControl, InputLabel, TextField,
  Table, TableHead, TableRow, TableCell, TableBody, Chip, Pagination, Typography,
} from "@mui/material";
import { Sources } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import { palette } from "../theme/kiwiTheme";

export default function SourceExplorer() {
  const [tables, setTables] = useState([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const PAGE_SIZE = 25;

  useEffect(() => {
    Sources.tables().then((t) => {
      setTables(t);
      if (t.length) setSelected(t[0].name);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    Sources.table(selected, { limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE, q: q || undefined }).then(setData);
  }, [selected, page, q]);

  return (
    <Box>
      <SectionHeader
        eyebrow="Raw Data Layer"
        title="Source Explorer"
        subtitle="Inspect the source-only synthetic tables underpinning all KPIs, AI prompts, and recommendations."
        actions={
          <Stack direction="row" spacing={1.5}>
            <FormControl size="small" sx={{ minWidth: 260 }}>
              <InputLabel>Table</InputLabel>
              <Select value={selected} label="Table" onChange={(e) => { setSelected(e.target.value); setPage(1); }} data-testid="source-table-select">
                {tables.map((t) => (
                  <MenuItem key={t.name} value={t.name}>
                    {t.name} ({t.rows})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              size="small"
              placeholder="Search text…"
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }}
              data-testid="source-search"
            />
          </Stack>
        }
      />
      {!data ? <LoadingState /> : (
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
              <Stack direction="row" spacing={1}>
                <Chip label={`Table: ${data.name}`} sx={{ fontFamily: "JetBrains Mono", fontSize: 11, bgcolor: palette.cream, fontWeight: 700 }} />
                <Chip label={`${data.total} rows`} sx={{ bgcolor: palette.surfaceAlt }} />
                <Chip label={`${data.columns.length} columns`} sx={{ bgcolor: palette.surfaceAlt }} />
              </Stack>
              <Pagination
                page={page}
                onChange={(_, p) => setPage(p)}
                count={Math.max(1, Math.ceil(data.total / PAGE_SIZE))}
                size="small"
                shape="rounded"
              />
            </Stack>
            <Box sx={{ overflowX: "auto" }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    {data.columns.map((c) => (
                      <TableCell key={c} sx={{ whiteSpace: "nowrap" }}>{c}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.items.map((row, i) => (
                    <TableRow key={i} hover>
                      {data.columns.map((c) => (
                        <TableCell key={c} sx={{ whiteSpace: "nowrap", maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis" }}>
                          {formatCell(row[c])}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

function formatCell(v) {
  if (v === null || v === undefined) return <Typography variant="caption" sx={{ color: palette.textMuted }}>—</Typography>;
  if (typeof v === "string" && v.length > 60) return v.slice(0, 60) + "…";
  if (typeof v === "number") return Number.isInteger(v) ? v : v.toFixed(3);
  return String(v);
}
