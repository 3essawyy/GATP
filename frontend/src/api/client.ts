// The only way the UI talks to the backend (ADR-002, ADR-013).
// Types in ./schema.d.ts are GENERATED from FastAPI's OpenAPI schema: never edit them by hand,
// run `uv run poe gen-client` after changing the API.
import createClient from 'openapi-fetch';

import type { components, paths } from './schema';

// Relative base URL: the Vite dev proxy (and later the production server) forwards /api.
export const api = createClient<paths>({ baseUrl: '/' });

export type Health = components['schemas']['Health'];
