/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#1CE783',
        'primary-dark': '#2ecf7a',
        'background-light': '#f6f8f7',
        'background-dark': '#0F1115',
        'surface-dark': '#1a2c24',
        'surface-light': '#ffffff',
        'card-dark': '#1a2c24',
        'card-darker': '#14261e',
        'accent-blue': '#44a8e9',
        'accent-purple': '#a844e9',
        'accent-gold': '#e9c444',
        'signal-amber': '#FFB020',
        'ai-blue': '#4DA3FF',
      },
      fontFamily: {
        display: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '1rem',
        xl: '1.5rem',
        '2xl': '2rem',
        full: '9999px',
      },
      boxShadow: {
        glow: '0 0 20px -5px rgba(68, 233, 150, 0.3)',
        'glow-lg': '0 0 50px 10px rgba(68, 233, 150, 0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        glow: 'glow 2s ease-in-out infinite alternate',
        shine: 'shine 2s infinite',
        fadeIn: 'fadeIn 1s ease-out forwards',
        slideRight: 'slideRight 1.5s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 20px -5px rgba(68, 233, 150, 0.3)' },
          '100%': { boxShadow: '0 0 50px 10px rgba(68, 233, 150, 0.15)' },
        },
        shine: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(200%)' },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(200%)' },
        },
      },
    },
  },
  plugins: [],
}
