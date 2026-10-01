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
          400: "#38bdf8", // GQT Cyan / Sky Blue accent
          500: "#0084ff", // GQT Electric Blue (top of 'Q')
          600: "#0066ff", // GQT Primary Vibrant Blue
          700: "#0047ba", // GQT Royal Sapphire (bottom of 'Q')
          800: "#003282", // GQT Deep Blue
          900: "#00214d", // GQT Signature Navy ('G' and 'GLOBAL QUEST')
          950: "#00132e", // GQT Midnight Base
        },
        gqt: {
          navy: "#00214d",     // 'G' & 'GLOBAL QUEST'
          blue: "#0066ff",     // 'Q' Primary Vibrant
          electric: "#0084ff", // 'Q' Top Gradient
          sapphire: "#0047ba", // 'Q' Bottom Gradient
          cyan: "#38bdf8",     // Accent Divider Lines
          charcoal: "#333a42", // 'T' & 'TECHNOLOGIES'
          steel: "#475569",    // 'TRAINING | INNOVATION | PLACEMENT'
          midnight: "#040812", // Deep Portal Canvas
        },
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          700: "#1b283d",
          800: "#0f1c30",
          850: "#0b1525",
          900: "#070e1b",
          950: "#040812", // GQT ultra dark midnight canvas
        },
        accent: {
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
          cyan: "#0084ff",
          indigo: "#4f46e5",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        "gqt-glow": "0 0 25px -5px rgba(0, 132, 255, 0.25)",
        "gqt-card": "0 8px 32px 0 rgba(0, 33, 77, 0.37)",
      }
    },
  },
  plugins: [],
}
