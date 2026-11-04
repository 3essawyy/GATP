import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

/** Subscribe to the project's Server-Sent Events and refresh affected queries. */
export function useProjectEvents(projectId: number) {
  const qc = useQueryClient();
  useEffect(() => {
    const source = new EventSource(`/api/projects/${projectId}/events`);
    const refresh = () => {
      qc.invalidateQueries({ queryKey: ['workflow', projectId] });
      qc.invalidateQueries({ queryKey: ['scope', projectId] });
      qc.invalidateQueries({ queryKey: ['pages', projectId] });
      qc.invalidateQueries({ queryKey: ['clarifications', projectId] });
      qc.invalidateQueries({ queryKey: ['snapshots'] });
      qc.invalidateQueries({ queryKey: ['insight', projectId] });
    };
    for (const kind of [
      'inspection_finished',
      'scope_saved',
      'approved',
      'artifact_changed',
      'clarification_answered',
      'page_added',
      'model_call_finished',
    ]) {
      source.addEventListener(kind, refresh);
    }
    return () => source.close();
  }, [projectId, qc]);
}
