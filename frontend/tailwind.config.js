module.exports = {
  content: [
    "../backend/finance_project/templates/**/*.html",
    "./src/**/*.{js,jsx}"
  ],
  theme: {
    extend: {},
  },
  plugins: [require('@tailwindcss/forms')],
}

