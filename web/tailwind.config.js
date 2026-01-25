/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        voxera: {
          brand: "#0f766e",
          "brand-light": "#14b8a6",
          "brand-dark": "#0d9488",
          surface: "#0f172a",
          "surface-elevated": "#1e293b",
          border: "#334155",
          muted: "#94a3b8",
        },
        latency: {
          good: "#22c55e",
          warn: "#eab308",
          bad: "#ef4444",
        },
      },
      animation: {
        "pulse-soft": "pulse-soft 1.5s ease-in-out infinite",
        "glow-speaking": "glow-speaking 1.2s ease-in-out infinite",
      },
      keyframes: {
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        "glow-speaking": {
          "0%, 100%": { boxShadow: "0 0 12px rgba(20, 184, 166, 0.3)" },
          "50%": { boxShadow: "0 0 24px rgba(20, 184, 166, 0.5)" },
        },
      },
    },
  },
  plugins: [],
};
