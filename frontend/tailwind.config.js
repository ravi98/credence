/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gpt: {
          sidebar: '#171717',
          sidebarHover: '#212121',
          bg: '#212121',
          surface: '#2f2f2f',
          input: '#2f2f2f',
          border: '#383838',
          text: '#ececec',
          subtext: '#b4b4b4',
          accent: '#10a37f', // OpenAI emerald
          accentHover: '#1a7f64'
        }
      }
    },
  },
  plugins: [],
}

