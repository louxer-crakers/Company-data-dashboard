import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
// 1. Impor adapter-node yang baru kamu install
import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    // 2. Gunakan adapter-node di sini
    adapter: adapter()
  }
};

export default config;