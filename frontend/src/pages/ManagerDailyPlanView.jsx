import React, { useEffect, useState } from "react";
import {
  Box, Card, CardContent, Grid, Typography, MenuItem, FormControl, Select, InputLabel,
  Table, TableHead, TableRow, TableCell, TableBody, Chip, Stack,
} from "@mui/material";
import SectionHeader from "../components/SectionHeader";
import LoadingState from "../components/LoadingState";
import { DailyPlanApi, RepApi } from "../services/api";

export default function ManagerDailyPlanView() {
  const [territory, setTerritory] = useState("");
  const [therapyArea, setTherapyArea] = useState("");
  const [repId, setRepId] = useState("");
  const [reps, setReps] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    RepApi.list().then((data) => {
      setReps(data);
      if (data.length && !repId) setRepId(data[0].rep_id);
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    DailyPlanApi.managerView({ territory, rep_id: repId, therapy_area: therapyArea })
      .then((data) => setPlans(data))
      .finally(() => setLoading(false));
  }, [territory, repId, therapyArea]);

  if (loading) return <LoadingState />;

  return (
    <Box>
      <SectionHeader
        eyebrow="Execution Oversight"
        title="Manager Daily Plan View"
        subtitle="Compare team plans, completion pressure, and coaching opportunities across reps."
      />

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Territory</InputLabel>
            <Select value={territory} label="Territory" onChange={(e) => setTerritory(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              {Array.from(new Set(reps.map((r) => r.territory))).map((territoryValue) => (
                <MenuItem key={territoryValue} value={territoryValue}>{territoryValue}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Rep</InputLabel>
            <Select value={repId} label="Rep" onChange={(e) => setRepId(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              {reps.map((rep) => (
                <MenuItem key={rep.rep_id} value={rep.rep_id}>{rep.rep_name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Therapy Area</InputLabel>
            <Select value={therapyArea} label="Therapy Area" onChange={(e) => setTherapyArea(e.target.value)}>
              <MenuItem value="">All</MenuItem>
              {Array.from(new Set(reps.map((r) => r.primary_therapy_area))).map((therapy) => (
                <MenuItem key={therapy} value={therapy}>{therapy}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Rep</TableCell>
                <TableCell>Territory</TableCell>
                <TableCell>Therapy</TableCell>
                <TableCell>Planned Actions</TableCell>
                <TableCell>High Priority</TableCell>
                <TableCell>Exp. Conversions</TableCell>
                <TableCell>Top Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {plans.map((plan) => (
                <TableRow key={plan.rep_id} hover>
                  <TableCell>{plan.rep_name}</TableCell>
                  <TableCell>{plan.territory}</TableCell>
                  <TableCell>{plan.primary_therapy_area}</TableCell>
                  <TableCell>{plan.summary?.total_planned_actions ?? 0}</TableCell>
                  <TableCell>{plan.summary?.high_priority_activities ?? 0}</TableCell>
                  <TableCell>{plan.summary?.expected_conversions ?? 0}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>{plan.top_actions?.[0]?.title ?? "—"}</Typography>
                      <Chip label={plan.top_actions?.[0]?.priority ?? ""} size="small" />
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Box>
  );
}
