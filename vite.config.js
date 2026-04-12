import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: "./postcss.config.js", // picks up your existing postcss/tailwind config
  },
  server: {
    port: 5173, // Vite's default port
    proxy: {
      "/api": "http://localhost:8000", // forwards to your Express brain
    },
  },
});