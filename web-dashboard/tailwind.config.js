/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk theme colors
        'space': {
          950: '#0a0e27',
          900: '#1a1f3a',
          800: '#252a48',
        },
        'neon': {
          cyan: '#00f7ff',
          magenta: '#ff00ff',
          green: '#00ff41',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': {
            'box-shadow': '0 0 5px theme(colors.neon.cyan), 0 0 10px theme(colors.neon.cyan), 0 0 15px theme(colors.neon.cyan)',
          },
          '100%': {
            'box-shadow': '0 0 10px theme(colors.neon.cyan), 0 0 20px theme(colors.neon.cyan), 0 0 30px theme(colors.neon.cyan)',
          },
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass': 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
