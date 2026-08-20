/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.html",
    "./pages/**/*.html",
    "./tools/**/*.html",
    "./recent-work/**/*.html",
    "./blog/*.html",
    "./js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1f3b4d',
        accent: '#4e9271',
      }
    }
  },
  plugins: [],
}
