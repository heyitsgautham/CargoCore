import path from 'node:path'
import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

const rootDir = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': path.resolve(rootDir, 'src') },
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.js'],
    setupFiles: ['tests/setup.js'],
    restoreMocks: true,
    unstubGlobals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text-summary', 'lcov'],
      include: ['src/config/**', 'src/utils/**', 'src/composables/**', 'src/stores/**'],
      exclude: ['src/utils/dummyData.js'],
      // Floor for the logic layer; raise it as the large role stores gain tests.
      thresholds: { statements: 10, branches: 5, functions: 11, lines: 11 },
    },
  },
})
