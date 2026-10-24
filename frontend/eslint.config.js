import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

export default [
  {
    ignores: ['dist/**', 'coverage/**', 'node_modules/**', 'html-slips/**', 'public/**'],
  },
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.{js,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        google: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', caughtErrors: 'none' }],
      'vue/multi-word-component-names': 'off',
      'no-empty': ['error', { allowEmptyCatch: true }],
    },
  },
  {
    files: [
      'vite.config.js',
      'vitest.config.js',
      'eslint.config.js',
      'tailwind.config.js',
      'postcss.config.mjs',
    ],
    languageOptions: { globals: globals.node },
  },
  {
    files: ['**/*.test.js', 'tests/**/*.js'],
    languageOptions: { globals: { ...globals.node, ...globals.vitest } },
  },
]
