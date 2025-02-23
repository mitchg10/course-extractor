import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { BASE_URL } from "./src/config/api";

// https://vitejs.dev/config/
// https://stackoverflow.com/questions/66389043/how-can-i-use-vite-env-variables-in-vite-config-js

export default defineConfig(({ mode }) => {
  const env = loadEnv("mock", process.cwd(), "");
  const processEnvValues = {
    "process.env": Object.entries(env).reduce((prev, [key, val]) => {
      console.log(key, val);
      return {
        ...prev,
        [key]: val,
      };
    }, {}),
  };
  return {
    plugins: [react()],
    base: "/",
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/api": {
          target: BASE_URL,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: "dist",
      assetsDir: "assets",
      sourcemap: mode === "development",
    },
    define: processEnvValues,
  };
});
