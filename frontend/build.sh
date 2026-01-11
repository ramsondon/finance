#!/bin/bash
set -e

echo "Building frontend..."

# Install dependencies
npm install

# Build CSS
npx tailwindcss -i ./src/index.css -o ../backend/finance_project/static/tailwind.css --minify

# Build JavaScript
npx esbuild src/index.jsx --bundle --outfile=../backend/finance_project/static/app.js --minify --sourcemap --loader:.jsx=jsx --jsx=automatic --jsx-import-source=react

echo "Frontend build complete!"

