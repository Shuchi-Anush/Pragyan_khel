import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Proxy all API calls to the FastAPI backend so hardcoded localhost is unnecessary
    proxy: {
      "/upload": { target: "http://localhost:8000", changeOrigin: true },
      "/video": { target: "http://localhost:8000", changeOrigin: true },
      "/download": { target: "http://localhost:8000", changeOrigin: true },
      "/report": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
