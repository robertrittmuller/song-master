import { Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { GeneratePage } from "./pages/GeneratePage";
import { LandingPage } from "./pages/LandingPage";
import { SongDetailPage } from "./pages/SongDetailPage";
import { PersonasPage } from "./pages/PersonasPage";

function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/personas" element={<PersonasPage />} />
        <Route path="/generate" element={<GeneratePage />} />
        <Route path="/songs/:songId" element={<SongDetailPage />} />
      </Routes>
    </AppLayout>
  );
}

export default App;
