module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
    ecmaFeatures: { jsx: true },
  },
  settings: {
    react: { version: "detect" },
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react/jsx-runtime",
  ],
  plugins: ["react"],
  rules: {
    "react/prop-types": "off",
    "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
  },
  ignorePatterns: [
    "dist",
    "node_modules",
    ".vite",
    "vite.config.js",
    "*.config.js",
  ],
};
