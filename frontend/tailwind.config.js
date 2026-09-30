/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f7ff",
          100: "#e0f0fe",
          200: "#bae3fd",
          300: "#7ccbfd",
          400: "#38b6f8",
          500: "#0284c7",
          600: "#0066ff", // GQT electric blue
          700: "#0052cc",
          800: "#003d99",
          900: "#002868", // GQT deep navy
          950: "#00173d",
        },
        gqt: {
          navy: "#002868",
          blue: "#0066ff",
          cyan: "#00d2ff",
          slate: "#334155",
          dark: "#00173d",
        },
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617", // deep editor dark
        },
        accent: {
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
          cyan: "#06b6d4",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
}
