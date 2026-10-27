// BACKEND_URL — Python backend manzili (real ishda alohida server bo'lishi mumkin)
const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: false },
  app: {
    head: {
      title: 'Mondi — kafe va yetkazib berish',
      htmlAttrs: { lang: 'uz' },
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
    },
  },
  routeRules: { '/api/**': { proxy: `${backend}/api/**` } },
})
