/** Shared Tailwind preset for VOXERA dashboard + web */
export default {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: { DEFAULT: "var(--card)", foreground: "var(--card-foreground)" },
        muted: { DEFAULT: "var(--muted)", foreground: "var(--muted-foreground)" },
        border: "var(--border)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
          hover: "var(--primary-hover)",
          muted: "var(--primary-muted)",
          "muted-foreground": "var(--primary-muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
          muted: "var(--accent-muted)",
          "muted-foreground": "var(--accent-muted-foreground)",
        },
        success: { DEFAULT: "var(--success)", muted: "var(--success-muted)" },
        warning: { DEFAULT: "var(--warning)", muted: "var(--warning-muted)" },
        destructive: { DEFAULT: "var(--destructive)", muted: "var(--destructive-muted)" },
        info: { DEFAULT: "var(--info)", muted: "var(--info-muted)" },
        hover: "var(--hover)",
        "background-subtle": "var(--background-subtle)",
        latency: { good: "var(--success)", warn: "var(--warning)", bad: "var(--destructive)" },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
        "display-lg": ["3rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        display: ["2.25rem", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
        headline: ["1.5rem", { lineHeight: "1.3", letterSpacing: "-0.01em" }],
        title: ["1.125rem", { lineHeight: "1.4" }],
        body: ["0.875rem", { lineHeight: "1.5" }],
        caption: ["0.75rem", { lineHeight: "1.4" }],
      },
      maxWidth: {
        content: "72rem",
        narrow: "40rem",
        wide: "80rem",
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.25rem",
      },
      boxShadow: {
        soft: "var(--shadow-soft)",
        "soft-lg": "var(--shadow-soft-lg)",
        "soft-xl": "var(--shadow-soft-xl)",
        "inner-soft": "var(--shadow-inner)",
      },
      transitionDuration: { 150: "150ms", 200: "200ms", 250: "250ms" },
      transitionTimingFunction: { smooth: "cubic-bezier(0.4, 0, 0.2, 1)" },
      spacing: {
        page: "var(--space-page)",
        section: "var(--space-section)",
        card: "var(--space-card)",
        element: "var(--space-element)",
        tight: "var(--space-tight)",
        4.5: "1.125rem",
        5.5: "1.375rem",
        7.5: "1.875rem",
        18: "4.5rem",
        22: "5.5rem",
        30: "7.5rem",
      },
      animation: {
        "fade-in": "fade-in 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        "fade-in-up": "fade-in-up 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
        "pulse-soft": "pulse-soft 1.5s ease-in-out infinite",
        "glow-speaking": "glow-speaking 1.2s ease-in-out infinite",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        "glow-speaking": {
          "0%, 100%": { boxShadow: "0 0 12px rgba(13, 148, 136, 0.3)" },
          "50%": { boxShadow: "0 0 24px rgba(13, 148, 136, 0.5)" },
        },
      },
    },
  },
};
