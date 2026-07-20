/** @type {import('tailwindcss').Config} */
const withAlpha = (v) => `rgb(var(${v}) / <alpha-value>)`;

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: withAlpha("--bg"),
        surface: {
          DEFAULT: withAlpha("--surface"),
          2: withAlpha("--surface-2"),
          3: withAlpha("--surface-3"),
        },
        overlay: withAlpha("--overlay"),
        content: {
          DEFAULT: withAlpha("--content"),
          muted: withAlpha("--content-muted"),
          subtle: withAlpha("--content-subtle"),
        },
        primary: {
          DEFAULT: withAlpha("--primary"),
          hover: withAlpha("--primary-hover"),
          active: withAlpha("--primary-active"),
          fg: withAlpha("--primary-fg"),
          subtle: withAlpha("--primary-subtle"),
        },
        success: { DEFAULT: withAlpha("--success"), fg: withAlpha("--success-fg") },
        warning: { DEFAULT: withAlpha("--warning"), fg: withAlpha("--warning-fg") },
        danger: { DEFAULT: withAlpha("--danger"), fg: withAlpha("--danger-fg") },
        info: { DEFAULT: withAlpha("--info"), fg: withAlpha("--info-fg") },
      },
      borderColor: {
        DEFAULT: withAlpha("--border"),
        strong: withAlpha("--border-strong"),
      },
      ringColor: { DEFAULT: withAlpha("--ring") },
      borderRadius: {
        sm: "calc(var(--radius) - 4px)",
        md: "calc(var(--radius) - 2px)",
        lg: "var(--radius)",
        xl: "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 10px)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        "elev-1": "0 1px 2px rgb(0 0 0 / 0.06), 0 1px 3px rgb(0 0 0 / 0.10)",
        "elev-2": "0 4px 12px -2px rgb(0 0 0 / 0.12), 0 2px 6px -2px rgb(0 0 0 / 0.08)",
        "elev-3": "0 16px 40px -12px rgb(0 0 0 / 0.20)",
        glow: "0 0 0 1px rgb(var(--primary) / 0.35), 0 10px 34px -10px rgb(var(--primary) / 0.40)",
        "glow-sm": "0 0 18px -6px rgb(var(--primary) / 0.55)",
      },
      keyframes: {
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out both",
        "slide-up": "slide-up 0.35s cubic-bezier(0.16, 1, 0.3, 1) both",
        "scale-in": "scale-in 0.2s cubic-bezier(0.16, 1, 0.3, 1) both",
        shimmer: "shimmer 1.5s infinite",
      },
    },
  },
  plugins: [],
};
