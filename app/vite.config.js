import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// GitHub Pages serves under https://<user>.github.io/<repo>/.
// VITE_BASE is set by the deploy workflow; locally we keep '/'.
const base = process.env.VITE_BASE ?? '/';

export default defineConfig({
  base,
  plugins: [react()],
  server: { port: 5173, host: true },
  // Force Vite to pre-bundle these so dynamic imports resolve to stable URLs.
  // Without this, the first click that triggers `import('xlsx')` etc. can fail
  // with "Failed to fetch dynamically imported module" after dep install.
  optimizeDeps: {
    include: ['xlsx', 'jszip', 'html-to-image'],
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          react:    ['react', 'react-dom', 'react-router-dom'],
          recharts: ['recharts'],
          maps:     ['react-simple-maps', 'd3-geo', 'd3-scale', 'd3-scale-chromatic'],
        },
      },
    },
  },
});
