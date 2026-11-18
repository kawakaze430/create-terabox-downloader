import { randomBytes } from "node:crypto";
import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

process.env.MANAGED_E2E_ACCESS_KEY ??= randomBytes(32).toString("hex");

export default defineConfig({
  ...base,
  testIgnore: [],
  testMatch: "**/managed-transfer-integration.spec.ts",
  webServer: [
    {
      command: "npm run start -- --hostname 127.0.0.1",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: "PYTHONPATH=../../services/api python ../../services/api/tests/serve_managed_transfer.py",
      url: "http://127.0.0.1:8000/healthz",
      reuseExistingServer: false,
      timeout: 15000,
    },
  ],
});
