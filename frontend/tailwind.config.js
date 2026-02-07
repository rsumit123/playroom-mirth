export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0E1111",
        slate: "#1A1F1F",
        fog: "#F6F4F1",
        mist: "#ECE8E2",
        accent: "#2C6E6A",
        accentLight: "#3F8E88"
      },
      fontFamily: {
        display: ["Playfair Display", "serif"],
        body: ["Manrope", "system-ui", "sans-serif"]
      },
      boxShadow: {
        soft: "0 12px 30px rgba(14, 17, 17, 0.08)",
        hover: "0 20px 45px rgba(14, 17, 17, 0.14)"
      },
      borderRadius: {
        xl: "16px"
      },
      keyframes: {
        floaty: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" }
        },
        glow: {
          "0%, 100%": { boxShadow: "0 0 0 rgba(44, 110, 106, 0.0)" },
          "50%": { boxShadow: "0 0 20px rgba(44, 110, 106, 0.35)" }
        },
        pop: {
          "0%": { transform: "scale(0.96)", opacity: 0 },
          "60%": { transform: "scale(1.02)", opacity: 1 },
          "100%": { transform: "scale(1)", opacity: 1 }
        },
        pulse: {
          "0%": { transform: "scale(1)", opacity: 0.6 },
          "70%": { transform: "scale(1.15)", opacity: 0 },
          "100%": { transform: "scale(1.15)", opacity: 0 }
        },
        sweep: {
          "0%": { transform: "translateX(-120%)" },
          "100%": { transform: "translateX(120%)" }
        }
      },
      animation: {
        floaty: "floaty 6s ease-in-out infinite",
        glow: "glow 2.8s ease-in-out infinite",
        pop: "pop 300ms ease-out",
        pulse: "pulse 2.6s ease-out infinite",
        sweep: "sweep 2.2s ease-in-out infinite"
      }
    }
  },
  plugins: []
}
