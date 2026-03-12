import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    viewportWidth: 1280,
    viewportHeight: 800,
    defaultCommandTimeout: 30000,
    responseTimeout: 60000,
  },
});
