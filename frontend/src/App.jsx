import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import AnalyticsPage from "./pages/AnalyticsPage";
import AssistantPage from "./pages/AssistantPage";
import DashboardPage from "./pages/DashboardPage";
import DocumentsPage from "./pages/DocumentsPage";
import GovernancePage from "./pages/GovernancePage";
import ImpactAnalysisPage from "./pages/ImpactAnalysisPage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";
import RegisterPage from "./pages/RegisterPage";
import RequirementsPage from "./pages/RequirementsPage";
import TraceabilityPage from "./pages/TraceabilityPage";
import ProtectedRoute from "./routes/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/documents"
            element={
              <ProtectedRoute>
                <DocumentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/requirements"
            element={
              <ProtectedRoute>
                <RequirementsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/traceability"
            element={
              <ProtectedRoute>
                <TraceabilityPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/assistant"
            element={
              <ProtectedRoute>
                <AssistantPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/:projectId/governance"
            element={
              <ProtectedRoute>
                <GovernancePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/impact"
            element={
              <ProtectedRoute>
                <ImpactAnalysisPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/analytics"
            element={
              <ProtectedRoute>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<ProtectedRoute><NotFoundPage /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
