/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F0F5FA',
          100: '#E1EBF5',
          200: '#C3D7EB',
          300: '#95B8DC',
          400: '#5F93CA',
          500: '#3A74B4',
          600: '#2A5B94',
          700: '#1E4473',
          800: '#153155',
          900: '#0F223D',
          950: '#0A172A',
        },
        loyalty: {
          bronze: '#8C5338',
          silver: '#71717A',
          gold: '#B4842E',
          platinum: '#475569',
        },
        slate: {
          850: '#151F30',
          900: '#0F172A',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
