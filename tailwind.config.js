/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand
        primary:       "var(--color-primary)",
        "primary-hover": "var(--color-primary-hover)",
        "primary-light": "var(--color-primary-light)",
        "primary-text":  "var(--color-primary-text)",
 
        // Backgrounds
        "bg-page":    "var(--color-bg-page)",
        "bg-surface": "var(--color-bg-surface)",
        "bg-subtle":  "var(--color-bg-subtle)",
        "bg-muted":   "var(--color-bg-muted)",
 
        // Borders
        "border-default": "var(--color-border-default)",
        "border-strong":  "var(--color-border-strong)",
 
        // Text
        "text-primary":   "var(--color-text-primary)",
        "text-secondary": "var(--color-text-secondary)",
        "text-muted":     "var(--color-text-muted)",
        "text-inverse":   "var(--color-text-inverse)",
 
        // Semantic
        success:         "var(--color-success)",
        "success-light": "var(--color-success-light)",
        "success-text":  "var(--color-success-text)",
        warning:         "var(--color-warning)",
        "warning-light": "var(--color-warning-light)",
        "warning-text":  "var(--color-warning-text)",
        danger:          "var(--color-danger)",
        "danger-light":  "var(--color-danger-light)",
        "danger-text":   "var(--color-danger-text)",
        info:            "var(--color-info)",
        "info-light":    "var(--color-info-light)",
        "info-text":     "var(--color-info-text)",
      },
 
      borderRadius: {
        sm:   "var(--radius-sm)",
        md:   "var(--radius-md)",
        lg:   "var(--radius-lg)",
        full: "var(--radius-full)",
      },
 
      fontFamily: {
        sans: "var(--font-sans)",
        mono: "var(--font-mono)",
      },
 
      width: {
        sidebar: "var(--sidebar-width)",
      },
 
      height: {
        tabbar: "var(--tab-bar-height)",
      },
    },
  },
  plugins: [],
}

