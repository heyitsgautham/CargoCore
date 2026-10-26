// Unit tests for the driver app's plain JavaScript logic: job state machine and order mapping.
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'driver-app',
    environment: 'node',
    include: ['tests/**/*.test.js'],
  },
})
