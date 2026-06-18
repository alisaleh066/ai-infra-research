import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0f1c",
          900: "#0d1422",
          800: "#142033",
          700: "#1d2c44",
          600: "#2a3c58",
        },
        paper: {
          DEFAULT: "#f6f3ec",
          dim: "#ece7db",
          line: "#dcd5c5",
        },
        gold: {
          DEFAULT: "#c69749",
          bright: "#d9ad5e",
          deep: "#9c7430",
        },
        slatey: "#8a93a6",
        data: {
          blue: "#5b8def",
          red: "#e0635a",
          teal: "#3fb4a4",
        },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
    },
  },
  plugins: [],
};

export default config;
