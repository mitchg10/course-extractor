import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
// https://stackoverflow.com/questions/66389043/how-can-i-use-vite-env-variables-in-vite-config-js

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const processEnvValues = {
    'process.env': {
      NODE_ENV: JSON.stringify(mode),
    }
  };

  const config = {
    plugins: [react()],
    base: "/",
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    build: {
      outDir: "dist",
      assetsDir: "assets",
      sourcemap: mode === "development",
    },
    define: {
      'process.env.NODE_ENV': JSON.stringify(mode),
    },
  };

  if (mode == "development") {
    config.server = {
      host: true,
      port: 5173,
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
        },
      },
    };
  }

  console.log(`Building in ${mode} mode with NODE_ENV=${mode}`);
  
  return config;
});
