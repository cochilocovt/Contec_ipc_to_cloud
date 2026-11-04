# Home lab guide: source

Source for `docs/home-lab-guide.html`, a single self-contained page (React + TypeScript, bundled with Parcel).

- `data.ts` holds every device, phase and task. Most edits only touch this file.
- `App.tsx` is the page; `index.css` its styles; `index.html` the shell.

To rebuild, ask Claude to rebuild the home lab guide with the web-artifacts-builder skill from these files. It creates a project with `init-artifact.sh`, copies these four files in, runs `bundle-artifact.sh`, then adds the Google Fonts link to the bundle's `<head>` after `<title>` (the bundler can't inline it). Copy the result over `docs/home-lab-guide.html`.
