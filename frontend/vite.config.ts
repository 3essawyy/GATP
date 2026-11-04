import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The UI calls relative `/api/...` URLs. In dev, Vite forwards them to the FastAPI app,
// so the browser sees one origin and no CORS round-trips are needed.
const apiTarget = process.env.GATP_API_URL ?? 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
    },
  },
});
