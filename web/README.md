# Parent Line website

The one-page site for Parent Line, built with [Astro](https://astro.build). Motion uses GSAP and Lenis; fonts are bundled, so the built site loads nothing from other servers.

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # static files in dist/
```

## Deploy

The build is plain static files, so any static host works.

- **Vercel or Netlify:** import the repo and set the root directory to `web`. Both detect Astro; the build command is `npm run build` and the output is `dist`.
- **Cloudflare Pages:** framework preset Astro, root directory `web`.

Page text lives in the components under `src/components/`; the alarm transcript and the room diagram read from `src/content.ts`.
