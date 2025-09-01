/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        "primary": 'var(--color-primary)',
        "teal": 'var(--color-teal)',
      },
      screens: {
        '3xl': '1920px',
      }
    },
  },
  plugins: [],
}