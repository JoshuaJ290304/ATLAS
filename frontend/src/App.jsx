import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { LoadingState } from "./components/UI";
import { AuthProvider } from "./context/AuthContext";
import AdminRoute from "./routes/AdminRoute";
import ProtectedRoute from "./routes/ProtectedRoute";

const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"));
const AdminAuditPage = lazy(() => import("./pages/admin/AdminAuditPage"));
const AdminDashboardPage = lazy(() => import("./pages/admin/AdminDashboardPage"));
const AdminProjectsPage = lazy(() => import("./pages/admin/AdminProjectsPage"));
const AdminSettingsPage = lazy(() => import("./pages/admin/AdminSettingsPage"));
const AdminSystemPage = lazy(() => import("./pages/admin/AdminSystemPage"));
const AdminUserDetailPage = lazy(() => import("./pages/admin/AdminUserDetailPage"));
const AdminUsersPage = lazy(() => import("./pages/admin/AdminUsersPage"));
const AssistantPage = lazy(() => import("./pages/AssistantPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const DocumentsPage = lazy(() => import("./pages/DocumentsPage"));
const ForgotPasswordPage = lazy(() => import("./pages/ForgotPasswordPage"));
const GovernancePage = lazy(() => import("./pages/GovernancePage"));
const ImpactAnalysisPage = lazy(() => import("./pages/ImpactAnalysisPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const ResetPasswordPage = lazy(() => import("./pages/ResetPasswordPage"));
const ReleaseReadinessPage = lazy(() => import("./pages/ReleaseReadinessPage"));
const RequirementsPage = lazy(() => import("./pages/RequirementsPage"));
const TestCasesPage = lazy(() => import("./pages/TestCasesPage"));
const TraceabilityPage = lazy(() => import("./pages/TraceabilityPage"));

function Protected({ children }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

function AdminOnly({ children }) {
  return <AdminRoute>{children}</AdminRoute>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<LoadingState label="Loading ATLAS..." />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            <Route path="/admin" element={<AdminOnly><AdminDashboardPage /></AdminOnly>} />
            <Route path="/admin/users" element={<AdminOnly><AdminUsersPage /></AdminOnly>} />
            <Route path="/admin/users/:userId" element={<AdminOnly><AdminUserDetailPage /></AdminOnly>} />
            <Route path="/admin/projects" element={<AdminOnly><AdminProjectsPage /></AdminOnly>} />
            <Route path="/admin/audit" element={<AdminOnly><AdminAuditPage /></AdminOnly>} />
            <Route path="/admin/system" element={<AdminOnly><AdminSystemPage /></AdminOnly>} />
            <Route path="/admin/settings" element={<AdminOnly><AdminSettingsPage /></AdminOnly>} />

            <Route path="/" element={<Protected><DashboardPage /></Protected>} />
            <Route path="/projects/:projectId/documents" element={<Protected><DocumentsPage /></Protected>} />
            <Route path="/projects/:projectId/requirements" element={<Protected><RequirementsPage /></Protected>} />
            <Route path="/projects/:projectId/test-cases" element={<Protected><TestCasesPage /></Protected>} />
            <Route path="/projects/:projectId/traceability" element={<Protected><TraceabilityPage /></Protected>} />
            <Route path="/projects/:projectId/assistant" element={<Protected><AssistantPage /></Protected>} />
            <Route path="/projects/:projectId/governance" element={<Protected><GovernancePage /></Protected>} />
            <Route path="/projects/:projectId/impact" element={<Protected><ImpactAnalysisPage /></Protected>} />
            <Route path="/projects/:projectId/releases" element={<Protected><ReleaseReadinessPage /></Protected>} />
            <Route path="/projects/:projectId/analytics" element={<Protected><AnalyticsPage /></Protected>} />
            <Route path="*" element={<Protected><NotFoundPage /></Protected>} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
