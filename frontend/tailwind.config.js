import forms from '@tailwindcss/forms'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Keep existing utility aliases while using one quiet, high-contrast palette.
      colors: {
        peach: { DEFAULT: '#2563EB', light: '#DBEAFE', dark: '#1D4ED8', muted: '#EFF6FF' },
        cream: { DEFAULT: '#F8FAFC', dark: '#F1F5F9' },
        dark: { DEFAULT: '#0F172A', light: '#1E293B', muted: '#475569' },
        glass: { bg: '#FFFFFF', border: '#E2E8F0', shadow: 'rgba(15,23,42,0.04)' },
      },
      fontFamily: { display: ['Inter', 'system-ui', 'sans-serif'], sans: ['Inter', 'system-ui', 'sans-serif'] },
      borderRadius: { card: '12px' },
      boxShadow: { card: '0 1px 2px rgba(15, 23, 42, 0.06)', glass: 'none', peach: 'none' },
    },
  },
  plugins: [forms],
}
