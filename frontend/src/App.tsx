import { Navigate, Route, Routes } from 'react-router';

import { InspectPage } from './pages/InspectPage';
import { NotYetPage } from './pages/NotYetPage';
import { ProjectLayout } from './pages/ProjectLayout';
import { ProjectsPage } from './pages/ProjectsPage';
import { ScopePage } from './pages/ScopePage';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<ProjectsPage />} />
      <Route path="/projects/:projectId" element={<ProjectLayout />}>
        <Route index element={<Navigate to="inspect" replace />} />
        <Route path="inspect" element={<InspectPage />} />
        <Route path="scope" element={<ScopePage />} />
        <Route path="plan" element={<NotYetPage what="Collaborative test design" />} />
        <Route path="code" element={<NotYetPage what="Code generation and review" />} />
      </Route>
    </Routes>
  );
}
