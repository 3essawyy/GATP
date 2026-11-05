import { Navigate, Route, Routes } from 'react-router';

import { CodePage } from './pages/CodePage';
import { InspectPage } from './pages/InspectPage';
import { MaintainPage } from './pages/MaintainPage';
import { PlanPage } from './pages/PlanPage';
import { ProjectLayout } from './pages/ProjectLayout';
import { ProjectsPage } from './pages/ProjectsPage';
import { RunPage } from './pages/RunPage';
import { ScopePage } from './pages/ScopePage';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<ProjectsPage />} />
      <Route path="/projects/:projectId" element={<ProjectLayout />}>
        <Route index element={<Navigate to="inspect" replace />} />
        <Route path="inspect" element={<InspectPage />} />
        <Route path="scope" element={<ScopePage />} />
        <Route path="plan" element={<PlanPage />} />
        <Route path="code" element={<CodePage />} />
        <Route path="run" element={<RunPage />} />
        <Route path="maintain" element={<MaintainPage />} />
      </Route>
    </Routes>
  );
}
