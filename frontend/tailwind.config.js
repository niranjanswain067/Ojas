/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        page: {
          light: "#FFFFFF",
          dark: "#14181F",
        },
        surface: {
          light: "#F5F7FA",
          dark: "#1C222B",
        },
        border: {
          light: "#D5DBE3",
          dark: "#2D3541",
        },
        content: {
          light: "#1B2430",
          dark: "#E6EAF0",
        },
        muted: {
          light: "#5F6B7A",
          dark: "#98A3B3",
        },
        primary: {
          light: "#1F3A5F",
          dark: "#6FA0E0",
          DEFAULT: "#1F3A5F",
        },
        success: {
          light: "#2E7D32",
          dark: "#66BB6A",
        },
        warning: {
          light: "#B26A00",
          dark: "#FFB74D",
        },
        danger: {
          light: "#C62828",
          dark: "#EF5350",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "Consolas",
          "Menlo",
          '"Liberation Mono"',
          '"Courier New"',
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

