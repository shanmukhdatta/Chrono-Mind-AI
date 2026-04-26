/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Inter', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      colors: {
        peach: '#F4A261',
        'deep-peach': '#E76F51',
        gold: '#E9C46A',
        teal: '#2A9D8F',
        cream: '#FFF8F3',
      },
    },
  },
  plugins: [],
}
