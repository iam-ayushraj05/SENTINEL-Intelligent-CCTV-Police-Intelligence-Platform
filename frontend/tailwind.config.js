/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        "bg-secondary": "var(--bg-secondary)",
        surface: "var(--surface)",
        "surface-hover": "var(--surface-hover)",
        "surface-active": "var(--surface-active)",
        border: "var(--border)",
        "border-light": "var(--border-light)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        subtle: "var(--subtle)",
        accent: "var(--accent)",
        cyan: "var(--accent-cyan)",
        success: "var(--success)",
        warning: "var(--warning)",
        danger: "var(--danger)",
        critical: "var(--critical)",
      },
      borderRadius: {
        DEFAULT: "8px",
        lg: "10px",
        xl: "12px",
      },
    },
  },
  plugins: [],
};
