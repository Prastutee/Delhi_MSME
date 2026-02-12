/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#334155', // Slate 700
          DEFAULT: '#0f172a', // Slate 900 (Deep Navy)
          dark: '#020617', // Slate 950
        },
        accent: {
          light: '#818cf8', // Indigo 400
          DEFAULT: '#6366f1', // Indigo 500
          dark: '#4f46e5', // Indigo 600
        },
        background: {
          DEFAULT: '#f8fafc', // Slate 50
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
