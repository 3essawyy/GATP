// One hook per endpoint. Components never call `fetch`; they use these hooks.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api, unwrap, type ScopeIn, type SetupStep } from './client';

const pid = (projectId: number) => ({ params: { path: { project_id: projectId } } });

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => unwrap(await api.GET('/api/health')),
    refetchInterval: 10_000,
    retry: false,
  });
}

export function useRunnerHealth() {
  return useQuery({
    queryKey: ['runner-health'],
    queryFn: async () => unwrap(await api.GET('/api/runner/health')),
    refetchInterval: 10_000,
    retry: false,
  });
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => unwrap(await api.GET('/api/projects')),
  });
}

export function useProject(projectId: number) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => unwrap(await api.GET('/api/projects/{project_id}', pid(projectId))),
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; url: string }) =>
      unwrap(await api.POST('/api/projects', { body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  });
}

export function useWorkflow(projectId: number) {
  return useQuery({
    queryKey: ['workflow', projectId],
    queryFn: async () =>
      unwrap(await api.GET('/api/projects/{project_id}/workflow', pid(projectId))),
  });
}

export function usePages(projectId: number) {
  return useQuery({
    queryKey: ['pages', projectId],
    queryFn: async () => unwrap(await api.GET('/api/projects/{project_id}/pages', pid(projectId))),
  });
}

export function useAddPage(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { url: string; name: string }) =>
      unwrap(await api.POST('/api/projects/{project_id}/pages', { ...pid(projectId), body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pages', projectId] }),
  });
}

export function useSetPageSetup(projectId: number, pageId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (steps: SetupStep[]) =>
      unwrap(
        await api.PUT('/api/pages/{page_id}/setup', {
          params: { path: { page_id: pageId } },
          body: { steps },
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pages', projectId] }),
  });
}

export function useSnapshots(pageId: number) {
  return useQuery({
    queryKey: ['snapshots', pageId],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/pages/{page_id}/snapshots', { params: { path: { page_id: pageId } } }),
      ),
  });
}

export function useSnapshot(snapshotId: number | undefined) {
  return useQuery({
    queryKey: ['snapshot', snapshotId],
    enabled: snapshotId !== undefined,
    queryFn: async () =>
      unwrap(
        await api.GET('/api/snapshots/{snapshot_id}', {
          params: { path: { snapshot_id: snapshotId ?? 0 } },
        }),
      ),
  });
}

export function useInspect(projectId: number, pageId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (scope: { include: string[]; exclude: string[] }) =>
      unwrap(
        await api.POST('/api/pages/{page_id}/inspections', {
          params: { path: { page_id: pageId } },
          body: { scope },
        }),
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['snapshots', pageId] });
      qc.invalidateQueries({ queryKey: ['workflow', projectId] });
    },
  });
}

export function useScope(projectId: number) {
  return useQuery({
    queryKey: ['scope', projectId],
    retry: false,
    // `null` until the tester saves a scope.
    queryFn: async () => unwrap(await api.GET('/api/projects/{project_id}/scope', pid(projectId))),
  });
}

export function useSaveScope(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ScopeIn) =>
      unwrap(await api.PUT('/api/projects/{project_id}/scope', { ...pid(projectId), body })),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['scope', projectId] });
      qc.invalidateQueries({ queryKey: ['workflow', projectId] });
      qc.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });
}

export function useApprove(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      gate: 'G0' | 'G1' | 'G2' | 'G3' | 'G4' | 'G5';
      actor: string;
      artifact_version_id?: number | null;
      comment?: string;
    }) =>
      unwrap(await api.POST('/api/projects/{project_id}/approvals', { ...pid(projectId), body })),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow', projectId] });
      qc.invalidateQueries({ queryKey: ['scope', projectId] });
      qc.invalidateQueries({ queryKey: ['approvals', projectId] });
    },
  });
}

export function useClarifications(projectId: number) {
  return useQuery({
    queryKey: ['clarifications', projectId],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/projects/{project_id}/clarifications', {
          params: { path: { project_id: projectId }, query: { status: 'open' } },
        }),
      ),
  });
}

export function useAnswer(projectId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (v: { id: number; answer: string; actor: string }) =>
      unwrap(
        await api.POST('/api/clarifications/{clarification_id}/answer', {
          params: { path: { clarification_id: v.id } },
          body: { answer: v.answer, actor: v.actor },
        }),
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clarifications', projectId] });
      qc.invalidateQueries({ queryKey: ['workflow', projectId] });
    },
  });
}

/** Raw text of a stored artifact file (e.g. the served page HTML for the source view). */
export function useFileText(path: string | undefined) {
  return useQuery({
    queryKey: ['file', path],
    enabled: !!path,
    staleTime: Infinity,
    queryFn: async () => {
      const resp = await fetch(`/api/files/${path}`);
      if (!resp.ok) throw new Error(`could not load ${path}`);
      return resp.text();
    },
  });
}
