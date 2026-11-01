/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#2D526E', // Slate blue
          hover: '#24445C',
          deep: '#1E2D39',   // Deep ink
          muted: '#63727C',  // Secondary text
          link: '#315E7A',
          icon: '#6F899A',
          light: '#EAF0F4',  // Pale blue
        },
        surface: {
          canvas: '#F7F8F6', // Warm white
          card: '#FFFFFF',
          secondary: '#EEF2F4',
          ivory: '#F4F1EA',
          border: '#DDE4E7'
        },
        sage: {
          DEFAULT: '#2F7658', // Verified green
          light: '#EAF0EA',
          border: '#C5DCCB'
        },
        accent: {
          warning: '#8D5A22',
          error: '#B34343',
          warm: '#B58A54'
        }
      },
      fontFamily: {
        sans: ['"Source Sans 3"', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
      }
    },
  },
  plugins: [],
}
