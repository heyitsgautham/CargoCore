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
      include: [
        'src/config/**',
        'src/utils/**',
        'src/composables/**',
        'src/stores/**',
        // Logic modules split out of the role views (Vue templates are checked in the browser).
        'src/*-views/**/*.js',
        'src/views/**/*.js',
      ],
      exclude: ['src/utils/dummyData.js'],
      // Floor for the logic layer; raise it as the large role stores gain tests.
      thresholds: { statements: 55, branches: 52, functions: 55, lines: 58 },
    },
  },
})
