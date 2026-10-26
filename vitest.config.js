// `npm test` from the repo root runs every workspace's Vitest project.
// Each project keeps its own config, so `npm test` inside frontend/ gives the same result.
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    projects: ['frontend', 'driver-app'],
  },
})
