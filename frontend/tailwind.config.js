/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        peach: {
          DEFAULT: '#E8A87C',
          light: '#FDDCB5',
          dark: '#D4895C',
          muted: '#F5D5C0'
        },
        cream: {
          DEFAULT: '#FDFAF7',
          dark: '#F5EDE6'
        },
        dark: {
          DEFAULT: '#1A1A2E',
          light: '#2D2D44',
          muted: '#555555'
        },
        glass: {
          bg: 'rgba(255, 255, 255, 0.55)',
          border: 'rgba(255, 255, 255, 0.75)',
          shadow: 'rgba(232, 168, 124, 0.12)'
        }
      },
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        sans: ['Inter', 'sans-serif'],
      },
      backdropBlur: {
        glass: '14px',
      },
      borderRadius: {
        card: '20px',
      },
      boxShadow: {
        card: '0 8px 32px rgba(0, 0, 0, 0.08)',
        glass: '0 4px 24px rgba(232, 168, 124, 0.12)',
        peach: '0 4px 20px rgba(232, 168, 124, 0.25)',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
      },
      keyframes: {
        float: {
          '0%': { transform: 'translateY(0px)' },
          '100%': { transform: 'translateY(-12px)' },
        },
        slideIn: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}