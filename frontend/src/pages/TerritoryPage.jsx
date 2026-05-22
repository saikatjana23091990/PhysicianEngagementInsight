import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, Grid, Typography, Stack, Chip, MenuItem, Select, FormControl, InputLabel,
  Table, TableHead, TableRow, TableCell, TableBody,
} from "@mui/material";
import { Territory, Conversion } from "../services/api";
import SectionHeader from "../components/SectionHeader";
import KPICard from "../components/KPICard";
import LoadingState from "../components/LoadingState";
import { palette, chartPalette } from "../theme/kiwiTheme";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";

export default function TerritoryPage() {
  const [territories, setTerritories] = useState([]);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState(null);
  const [heatmap, setHeatmap] = useState([]);

  useEffect(() => {
    Territory.list().then((d) => {
      setTerritories(d);
      if (d.length) setSelected(d[0].territory);
    });
    Territory.heatmap().then(setHeatmap);
  }, []);

  useEffect(() => {
    if (selected) Territory.detail(selected).then(setDetail);
  }, [selected]);

  if (!territories.length) return <LoadingState />;

  return (
    <Box>
      <SectionHeader
        eyebrow="Geographic Performance"
        title="Territory Analytics"
        subtitle="Cross-territory conversion benchmarks with deep dive per territory."
        actions={
          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>Territory</InputLabel>
            <Select value={selected} onChange={(e) => setSelected(e.target.value)} label="Territory" data-testid="territory-select">
              {territories.map((t) => (
                <MenuItem key={t.territory} value={t.territory}>
                  {t.territory} · {t.region} · {t.hcps} HCPs
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        }
      />

      <Card sx={{ mb: 2.5 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>Conversion Rate by Territory</Typography>
          <Box sx={{ height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={heatmap}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4ECE6" />
                <XAxis dataKey="territory" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} unit="%" />
                <Tooltip formatter={(v) => v?.toFixed?.(1) + "%"} />
                <Bar dataKey="conversion_rate" radius={[8, 8, 0, 0]}>
                  {heatmap.map((r, i) => (
                    <Cell key={i} fill={r.territory === selected ? palette.primary : chartPalette[i % chartPalette.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>

      {detail && (
        <>
          <Grid container spacing={2.5} sx={{ mb: 2 }}>
            <Grid item xs={6} md={3}><KPICard label="HCPs" value={detail.hcp_count} accent={palette.primary} /></Grid>
            <Grid item xs={6} md={3}><KPICard label="Calls" value={detail.total_calls} accent={palette.accent} /></Grid>
            <Grid item xs={6} md={3}><KPICard label="Converted" value={detail.converted_calls} accent={palette.light} /></Grid>
            <Grid item xs={6} md={3}><KPICard label="Rate" value={detail.conversion_rate?.toFixed(1)} unit="%" accent={palette.cream} /></Grid>
          </Grid>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontFamily: "Sora", mb: 1 }}>HCPs in {detail.territory}</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>HCP</TableCell>
                    <TableCell>Specialty</TableCell>
                    <TableCell>Hospital</TableCell>
                    <TableCell>Consent</TableCell>
                    <TableCell>Digital</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {detail.hcps_sample.map((h) => (
                    <TableRow key={h.hcp_id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{h.hcp_name}</TableCell>
                      <TableCell>{h.specialty_group}</TableCell>
                      <TableCell>{h.affiliated_hospital}</TableCell>
                      <TableCell>
                        <Chip size="small" label={h.consent_status}
                          color={h.consent_status === "Opted-in" ? "success" : h.consent_status === "Opted-out" ? "error" : "default"}/>
                      </TableCell>
                      <TableCell><Chip size="small" label={h.digital_engagement_tier} sx={{ bgcolor: palette.surfaceAlt }}/></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
}
