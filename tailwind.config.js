/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.html",
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
