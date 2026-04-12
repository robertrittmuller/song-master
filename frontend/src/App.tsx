import { ReactNode } from "react";
import { Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";

import { AppLayout } from "./components/layout/AppLayout";
import { useAuth } from "./features/auth/AuthProvider";
import { DashboardPage } from "./pages/DashboardPage";
import { GeneratePage } from "./pages/GeneratePage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { SongDetailPage } from "./pages/SongDetailPage";
import { PersonasPage } from "./pages/PersonasPage";
import { SongProposalsPage } from "./pages/SongProposalsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SignupPage } from "./pages/SignupPage";

function SongDetailRoute() {
  const { songId } = useParams();

  return <SongDetailPage key={songId} />;
}

function AuthScreenLoader() {
  return (
    <div className="auth-loading-screen">
      <div className="auth-loading-screen__panel card">
        <img src="/logo.png" alt="Song Master" className="auth-loading-screen__logo" />
        <p>Loading your workspace...</p>
      </div>
    </div>
  );
}

function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <AuthScreenLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />;
  }

  return <>{children}</>;
}

function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <AuthScreenLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

function ProtectedApp() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/proposals" element={<SongProposalsPage />} />
        <Route path="/personas" element={<PersonasPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/generate" element={<GeneratePage />} />
        <Route path="/songs/:songId" element={<SongDetailRoute />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}

function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={(
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        )}
      />
      <Route
        path="/signup"
        element={(
          <PublicOnlyRoute>
            <SignupPage />
          </PublicOnlyRoute>
        )}
      />
      <Route
        path="*"
        element={(
          <RequireAuth>
            <ProtectedApp />
          </RequireAuth>
        )}
      />
    </Routes>
  );
}

export default App;
