import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, TextField, Stack, Chip, MenuItem, Select, FormControl, InputLabel,
  Table, TableHead, TableRow, TableCell, TableBody, IconButton, Tooltip, Avatar,
} from "@mui/material";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import EventAvailableRoundedIcon from "@mui/icons-material/EventAvailableRounded";
import { Link } from "react-router-dom";
import { HCPApi } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import { palette } from "../theme/kiwiTheme";

export default function HCPDirectory() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [consent, setConsent] = useState("");
  const [specs, setSpecs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { HCPApi.specialties().then(setSpecs); }, []);

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      HCPApi.list({ q, specialty, consent, limit: 200 })
        .then((d) => { setItems(d.items); setTotal(d.total); })
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(t);
  }, [q, specialty, consent]);

  return (
    <Box>
      <SectionHeader
        eyebrow="Healthcare Professionals"
        title="HCP Directory"
        subtitle="Search, filter, and open a 360° HCP view. Open a Pre-Call Briefing in one click."
      />
      <Card sx={{ mb: 2.5 }}>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} alignItems={{ md: "center" }}>
            <TextField
              data-testid="hcp-search"
              size="small"
              fullWidth
              label="Search by name or ID"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Specialty</InputLabel>
              <Select label="Specialty" value={specialty} onChange={(e) => setSpecialty(e.target.value)} data-testid="hcp-specialty">
                <MenuItem value=""><em>All</em></MenuItem>
                {specs.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Consent</InputLabel>
              <Select label="Consent" value={consent} onChange={(e) => setConsent(e.target.value)} data-testid="hcp-consent">
                <MenuItem value=""><em>All</em></MenuItem>
                <MenuItem value="Opted-in">Opted-in</MenuItem>
                <MenuItem value="Opted-out">Opted-out</MenuItem>
                <MenuItem value="Pending">Pending</MenuItem>
              </Select>
            </FormControl>
            <Chip label={`${total} HCPs`} sx={{ bgcolor: palette.cream, fontWeight: 700 }} />
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ p: 0 }}>
          {loading ? <LoadingState /> : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>HCP</TableCell>
                  <TableCell>Specialty</TableCell>
                  <TableCell>Hospital</TableCell>
                  <TableCell>Region</TableCell>
                  <TableCell>Territory</TableCell>
                  <TableCell>Consent</TableCell>
                  <TableCell>Digital</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((h) => (
                  <TableRow key={h.hcp_id} hover data-testid={`hcp-row-${h.hcp_id}`}>
                    <TableCell>
                      <Stack direction="row" alignItems="center" spacing={1.2}>
                        <Avatar sx={{ width: 30, height: 30, bgcolor: palette.light, color: palette.primaryDark, fontSize: 13, fontWeight: 700 }}>
                          {h.hcp_name?.[0]}
                        </Avatar>
                        <Box>
                          <Box sx={{ fontWeight: 700 }}>{h.hcp_name}</Box>
                          <Box sx={{ fontSize: 11, color: palette.textMuted }}>{h.hcp_id}</Box>
                        </Box>
                      </Stack>
                    </TableCell>
                    <TableCell>{h.specialty_group}</TableCell>
                    <TableCell>{h.affiliated_hospital}</TableCell>
                    <TableCell>{h.region}</TableCell>
                    <TableCell>{h.territory}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={h.consent_status}
                        color={h.consent_status === "Opted-in" ? "success" : h.consent_status === "Opted-out" ? "error" : "default"}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip size="small" label={h.digital_engagement_tier} sx={{ bgcolor: palette.surfaceAlt }} />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View HCP detail">
                        <IconButton component={Link} to={`/hcp/${h.hcp_id}`} size="small" data-testid={`view-hcp-${h.hcp_id}`}>
                          <VisibilityRoundedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Pre-call briefing">
                        <IconButton component={Link} to={`/briefing/${h.hcp_id}`} size="small" data-testid={`brief-hcp-${h.hcp_id}`} sx={{ color: palette.accent }}>
                          <EventAvailableRoundedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
