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
        accentLight: "#3F8E88",
        accentDark: "#1F524F",
        gold: "#D4A843",
        silver: "#A0A5A5",
        bronze: "#B87333",
        correct: "#16A34A",
        danger: "#EF4444",
        purple: "#7C3AED"
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
        },
        "countdown-shake": {
          "0%, 100%": { transform: "translateX(0)" },
          "25%": { transform: "translateX(-2px)" },
          "75%": { transform: "translateX(2px)" }
        },
        "slide-up": {
          "0%": { transform: "translateY(12px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        },
        "scale-in": {
          "0%": { transform: "scale(0.8)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" }
        },
        "trophy-bounce": {
          "0%": { transform: "scale(0) rotate(-15deg)" },
          "50%": { transform: "scale(1.2) rotate(5deg)" },
          "100%": { transform: "scale(1) rotate(0)" }
        },
        "alert-in": {
          "0%": { transform: "translateY(-100%) scale(0.95)", opacity: "0" },
          "100%": { transform: "translateY(0) scale(1)", opacity: "1" }
        },
        "alert-out": {
          "0%": { transform: "translateY(0) scale(1)", opacity: "1" },
          "100%": { transform: "translateY(-100%) scale(0.95)", opacity: "0" }
        },
        "word-pulse": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(44, 110, 106, 0.05)", borderColor: "rgba(44, 110, 106, 0.2)" },
          "50%": { boxShadow: "0 0 24px 4px rgba(44, 110, 106, 0.12)", borderColor: "rgba(44, 110, 106, 0.45)" }
        },
        "input-glow": {
          "0%, 100%": { boxShadow: "inset 0 0 0 1.5px rgba(44, 110, 106, 0.2), 0 0 0 0 rgba(44, 110, 106, 0)" },
          "50%": { boxShadow: "inset 0 0 0 2.5px rgba(44, 110, 106, 0.55), 0 0 16px 0 rgba(44, 110, 106, 0.15)" }
        }
      },
      animation: {
        floaty: "floaty 6s ease-in-out infinite",
        glow: "glow 2.8s ease-in-out infinite",
        pop: "pop 300ms ease-out",
        pulse: "pulse 2.6s ease-out infinite",
        sweep: "sweep 2.2s ease-in-out infinite",
        "countdown-shake": "countdown-shake 0.3s ease-in-out",
        "slide-up": "slide-up 0.3s ease-out",
        "scale-in": "scale-in 0.3s ease-out",
        "trophy-bounce": "trophy-bounce 0.5s ease-out",
        "alert-in": "alert-in 0.35s ease-out forwards",
        "alert-out": "alert-out 0.3s ease-in forwards",
        "word-pulse": "word-pulse 2.5s ease-in-out infinite",
        "input-glow": "input-glow 2s ease-in-out infinite"
      }
    }
  },
  plugins: []
}
