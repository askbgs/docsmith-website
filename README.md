# Docsmith website

Landing page (`/`), purchase form (`/buy`), live demo (`/demo`), privacy policy (`/privacy`) and a 404 page, served by a dependency-free
Node server (`server.js`). The trial form posts to the n8n webhook
`https://n8n.srv834342.hstgr.cloud/webhook-test/docsmith-trial` (test URL; switch to `/webhook/` after publishing the n8n workflow).

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

## Purchase flow

- `/buy?plan=pro|enterprise` posts JSON to the n8n workflow **Docsmith – Purchase Requests**
  (`WEBHOOK` at the bottom of `public/buy.html`; switch `/webhook-test/` to `/webhook/` after publishing).
- The prices shown on `/buy` (`PRICE`, `FOUNDING` in `public/buy.html`) are only an estimate; the invoice
  amount comes from the workflow's **Settings** node. Keep them the same.
- `public/assets/docsmith-business-templates.json` holds the proforma/invoice and licence-certificate
  layouts plus the logo. Both n8n workflows download it and send it to the render server, so you can
  change the documents by editing `samples/business.js` and regenerating this file.
