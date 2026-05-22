import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ExecutiveDashboard from "./pages/ExecutiveDashboard";
import RepDashboard from "./pages/RepDashboard";
import HCPDirectory from "./pages/HCPDirectory";
import HCPDetail from "./pages/HCPDetail";
import PreCallBriefing from "./pages/PreCallBriefing";
import TerritoryPage from "./pages/TerritoryPage";
import NBAPage from "./pages/NBAPage";
import ConversionAnalytics from "./pages/ConversionAnalytics";
import KOLAnalytics from "./pages/KOLAnalytics";
import SourceExplorer from "./pages/SourceExplorer";
import ConversationalAnalytics from "./pages/ConversationalAnalytics";
import AdminSettings from "./pages/AdminSettings";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/executive" replace />} />
        <Route path="/executive" element={<ExecutiveDashboard />} />
        <Route path="/rep" element={<RepDashboard />} />
        <Route path="/hcp" element={<HCPDirectory />} />
        <Route path="/hcp/:hcpId" element={<HCPDetail />} />
        <Route path="/briefing" element={<PreCallBriefing />} />
        <Route path="/briefing/:hcpId" element={<PreCallBriefing />} />
        <Route path="/territory" element={<TerritoryPage />} />
        <Route path="/nba" element={<NBAPage />} />
        <Route path="/conversion" element={<ConversionAnalytics />} />
        <Route path="/kol" element={<KOLAnalytics />} />
        <Route path="/sources" element={<SourceExplorer />} />
        <Route path="/chat" element={<ConversationalAnalytics />} />
        <Route path="/settings" element={<AdminSettings />} />
      </Routes>
    </AppLayout>
  );
}
