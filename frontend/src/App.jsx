import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import AnalyticsPage from "./pages/AnalyticsPage";
import AdminAuditPage from "./pages/admin/AdminAuditPage";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AdminProjectsPage from "./pages/admin/AdminProjectsPage";
import AdminSettingsPage from "./pages/admin/AdminSettingsPage";
import AdminSystemPage from "./pages/admin/AdminSystemPage";
import AdminUserDetailPage from "./pages/admin/AdminUserDetailPage";
import AdminUsersPage from "./pages/admin/AdminUsersPage";
import AssistantPage from "./pages/AssistantPage";
import DashboardPage from "./pages/DashboardPage";
import DocumentsPage from "./pages/DocumentsPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import GovernancePage from "./pages/GovernancePage";
import ImpactAnalysisPage from "./pages/ImpactAnalysisPage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";
import RegisterPage from "./pages/RegisterPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import ReleaseReadinessPage from "./pages/ReleaseReadinessPage";
import RequirementsPage from "./pages/RequirementsPage";
import TraceabilityPage from "./pages/TraceabilityPage";
import TestCasesPage from "./pages/TestCasesPage";
import AdminRoute from "./routes/AdminRoute";
import ProtectedRoute from "./routes/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          <Route path="/admin" element={<AdminRoute><AdminDashboardPage /></AdminRoute>} />
          <Route path="/admin/users" element={<AdminRoute><AdminUsersPage /></AdminRoute>} />
          <Route path="/admin/users/:userId" element={<AdminRoute><AdminUserDetailPage /></AdminRoute>} />
          <Route path="/admin/projects" element={<AdminRoute><AdminProjectsPage /></AdminRoute>} />
          <Route path="/admin/audit" element={<AdminRoute><AdminAuditPage /></AdminRoute>} />
          <Route path="/admin/system" element={<AdminRoute><AdminSystemPage /></AdminRoute>} />
          <Route path="/admin/settings" element={<AdminRoute><AdminSettingsPage /></AdminRoute>} />
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
            path="/projects/:projectId/test-cases"
            element={
              <ProtectedRoute>
                <TestCasesPage />
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
            path="/projects/:projectId/releases"
            element={
              <ProtectedRoute>
                <ReleaseReadinessPage />
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
