import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Vite dev server (5173) and the FastAPI backend (8000) are separate
// processes on different origins. Rather than make cross-origin requests from
// the browser (which would need CORS), we let Vite proxy any request the app
// makes to "/process" through to the backend. The browser only ever talks to
// Vite's own origin, so there is no CORS to deal with in development.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/process": "http://localhost:8000",
    },
  },
});
