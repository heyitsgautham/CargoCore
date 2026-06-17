import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'

// Serve html-slips/ as static files under /html-slips/ during dev & build
function htmlSlipsPlugin() {
  let outDir = path.join(__dirname, 'dist')
  return {
    name: 'html-slips-static',
    configResolved(config) {
      outDir = path.resolve(config.root, config.build.outDir)
    },
    configureServer(server) {
      server.middlewares.use('/html-slips', (req, res, next) => {
        const filePath = path.join(__dirname, 'html-slips', req.url.replace(/^\//, ''))
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          const ext = path.extname(filePath)
          const mime = ext === '.html' ? 'text/html' : ext === '.png' ? 'image/png' : ext === '.jpeg' || ext === '.jpg' ? 'image/jpeg' : 'application/octet-stream'
          res.setHeader('Content-Type', mime)
          fs.createReadStream(filePath).pipe(res)
        } else {
          next()
        }
      })
    },
    writeBundle() {
      const srcDir = path.join(__dirname, 'html-slips')
      const destDir = path.join(outDir, 'html-slips')
      fs.mkdirSync(destDir, { recursive: true })
      fs.cpSync(srcDir, destDir, { recursive: true })
    }
  }
}

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    htmlSlipsPlugin(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  assetsInclude: ['**/*.svg', '**/*.csv'],
})
