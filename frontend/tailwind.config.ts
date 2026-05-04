/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0A0F1C',
          900: '#111827',
          800: '#1a2234',
          700: '#2d3e5a',
          600: '#3d5070',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fadein': 'fadeIn 0.2s ease both',
        'slidein': 'slideIn 0.2s ease both',
      },
    },
  },
  plugins: [],
}
