import { defineConfig } from 'vite'
import { resolve } from 'path'//https://vitejs.dev/config/export default defineConfig({//Base public path when served in development or production
  base: '/',//Build configuration
  build: {//Output directory for build files
    outDir: 'dist',//Generate sourcemaps for production build
    sourcemap: true,//Minify the output
    minify: 'terser',//Rollup options
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
      output: {//Manual chunks for better caching
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },//Target browsers
    target: 'es2015',//Asset inline threshold
    assetsInlineLimit: 4096,
  },//Development server configuration
  server: {
    port: 3000,
    host: true,
    open: true,
    cors: true,
  },//Preview server configuration
  preview: {
    port: 4173,
    host: true,
  },//Environment variables
  envPrefix: 'VITE_',//CSS configuration
  css: {
    devSourcemap: true,
    preprocessorOptions: {
      scss: {
        additionalData: `@import "./src/styles/variables.scss";`
      }
    }
  },//Plugin configuration
  plugins: [],//Resolve configuration
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@assets': resolve(__dirname, 'src/assets'),
    },
  },//Optimization
  optimizeDeps: {
    include: ['react', 'react-dom'],
  },//Define global constants
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_DATE__: JSON.stringify(new Date().toISOString()),
  },
})