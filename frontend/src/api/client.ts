// The only way the UI talks to the backend (ADR-002, ADR-013).
// Types in ./schema.d.ts are GENERATED from FastAPI's OpenAPI schema: never edit them by hand,
// run `uv run poe gen-client` after changing the API.
import createClient from 'openapi-fetch';

import type { components, paths } from './schema';

// Relative base URL: the Vite dev proxy (and later the production server) forwards /api.
export const api = createClient<paths>({ baseUrl: '/' });

type S = components['schemas'];
export type Health = S['Health'];
export type RunnerHealth = S['RunnerHealth'];
export type Project = S['ProjectOut'];
export type Page = S['PageOut'];
export type Snapshot = S['SnapshotOut'];
export type SnapshotSummary = S['SnapshotSummary'];
export type Element = S['ElementOut'];
export type Locator = S['LocatorOut'];
export type Inspection = S['InspectionOut'];
export type Scope = S['ScopeOut'];
export type ScopeIn = S['ScopeIn'];
export type Step = S['StepOut'];
export type SetupStep = S['SetupStep'];
export type Clarification = S['ClarificationOut'];
export type Approval = S['ApprovalOut'];

/** Error shape returned by the API (`{"error": code, "detail": message}`). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    detail: string,
  ) {
    super(detail);
  }
}

/** Turn an openapi-fetch result into data or a thrown ApiError (for TanStack Query). */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || result.data === undefined) {
    const body = (result.error ?? {}) as { error?: string; detail?: unknown };
    const detail =
      typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body);
    throw new ApiError(result.response.status, body.error ?? 'error', detail);
  }
  return result.data;
}

/** URL of a stored artifact file (screenshot, page HTML). */
export const fileUrl = (path: string) => `/api/files/${path}`;
export type InsightResult = S['InsightOut'];
export type LlmCall = S['LlmCallOut'];
