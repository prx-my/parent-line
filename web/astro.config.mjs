import { defineConfig } from "astro/config";

// Static output: `npm run build` writes plain files to dist/, which any static host serves.
// Code blocks in blog posts are styled by the site, so no colour theme is added.
export default defineConfig({ markdown: { syntaxHighlight: false } });
