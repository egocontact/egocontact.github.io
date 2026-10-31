import { enhancedImages } from "@sveltejs/enhanced-img";
import adapter from "@sveltejs/adapter-static";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

const projectDirectory = decodeURIComponent(new URL(".", import.meta.url).pathname);

export default defineConfig({
  server: {
    watch: {
      // Raw datasets and reference checkouts are not application sources.
      ignored: [`${projectDirectory}data/**`, `${projectDirectory}tmp/**`],
      followSymlinks: false,
    },
  },
  plugins: [
    enhancedImages(),
    sveltekit({
      compilerOptions: {
        // Force runes mode for the project, except for libraries. Can be removed in svelte 6.
        runes: ({ filename }) =>
          filename.split(/[/\\]/).includes("node_modules") ? undefined : true,
      },

      adapter: adapter(),
    }),
  ],
});
