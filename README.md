# Docsmith website

Landing page (`/`), privacy policy (`/privacy`) and a 404 page, served by a dependency-free
Node server (`server.js`). The trial form posts to the n8n webhook
`https://n8n.srv834342.hstgr.cloud/webhook/docsmith-trial`.

## Run locally
```bash
node server.js            # http://localhost:8080
```

## Deploy to Railway
1. Push this folder to a new GitHub repository (e.g. `docsmith-website`).
2. railway.com → New Project → Deploy from GitHub repo → pick it. `railway.json` sets the start
   command and the `/health` check; no variables are needed (Railway sets `PORT`).
3. Service → Settings → Networking → Generate Domain (or add your own domain, e.g. `docsmith.lk`,
   and create the CNAME record Railway shows).
4. Optional: Variables → `NODE_ENV=production` (keeps files cached in memory).

Updating: edit the files in `public/`, commit and push; Railway redeploys.
The landing page is built from the Design canvas with `tools/build_site.py` (see the header of that file).
