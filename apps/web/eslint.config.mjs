import nextTypescript from "eslint-config-next/typescript";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

const eslintConfig = [
  ...nextTypescript,
  ...nextCoreWebVitals,
  // Global ignores
  {
    ignores: ["node_modules", ".next", "out", "dist"],
  },
  // Relax rules for pre-existing code issues
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": "warn",
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];

export default eslintConfig;
