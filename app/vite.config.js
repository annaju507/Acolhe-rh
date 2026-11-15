import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Porta própria do Acolhe, para não confundir com outros projetos abertos.
  server: { port: 5180, strictPort: true, open: true },
})
