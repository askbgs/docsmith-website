'use strict';
/*
 * Docsmith website – tiny static server for Railway (no dependencies).
 *   /            -> public/index.html
 *   /privacy     -> public/privacy.html   (/privacy.html redirects here)
 *   /assets/*    -> public/assets/*       (cached for a week)
 *   /health      -> "ok"                  (Railway health check)
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const PORT = Number(process.env.PORT) || 8080;
const ROOT = path.join(__dirname, 'public');
const WEBHOOK_ORIGIN = 'https://n8n.srv834342.hstgr.cloud';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.ico': 'image/x-icon', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml; charset=utf-8', '.json': 'application/json'
};
const ROUTES = { '/': 'index.html', '/privacy': 'privacy.html' };
const REDIRECTS = { '/index.html': '/', '/privacy.html': '/privacy', '/privacy-policy': '/privacy' };

const SECURITY = {
  'Content-Security-Policy': [
    "default-src 'self'",
    "img-src 'self' data:",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "script-src 'self' 'unsafe-inline'",
    'connect-src ' + WEBHOOK_ORIGIN,
    "form-action 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'"
  ].join('; '),
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), interest-cohort=()'
};

const cache = new Map();   // path -> { body, gz, type }
function load(file) {
  if (cache.has(file)) return cache.get(file);
  const body = fs.readFileSync(file);
  const type = TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream';
  const gz = /text|svg|json|xml/.test(type) ? zlib.gzipSync(body) : null;
  const entry = { body, gz, type };
  if (process.env.NODE_ENV === 'production') cache.set(file, entry);
  return entry;
}

function send(req, res, status, file, extra) {
  const f = load(file);
  const headers = Object.assign({ 'Content-Type': f.type, Vary: 'Accept-Encoding' }, SECURITY, extra || {});
  let body = f.body;
  if (f.gz && /\bgzip\b/.test(req.headers['accept-encoding'] || '')) { body = f.gz; headers['Content-Encoding'] = 'gzip'; }
  headers['Content-Length'] = body.length;
  res.writeHead(status, headers);
  res.end(req.method === 'HEAD' ? undefined : body);
}

http.createServer((req, res) => {
  let url;
  try { url = new URL(req.url, 'http://x'); } catch (e) { res.writeHead(400); return res.end(); }
  const p = decodeURIComponent(url.pathname);
  if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405, { Allow: 'GET, HEAD' }); return res.end(); }
  if (p === '/health') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('ok'); }
  if (REDIRECTS[p]) { res.writeHead(301, { Location: REDIRECTS[p] + url.search }); return res.end(); }

  if (ROUTES[p]) return send(req, res, 200, path.join(ROOT, ROUTES[p]), { 'Cache-Control': 'no-cache' });

  const file = path.normalize(path.join(ROOT, p));
  if (file.startsWith(ROOT + path.sep) && fs.existsSync(file) && fs.statSync(file).isFile()) {
    const long = p.startsWith('/assets/');
    return send(req, res, 200, file, { 'Cache-Control': long ? 'public, max-age=604800' : 'no-cache' });
  }
  return send(req, res, 404, path.join(ROOT, '404.html'), { 'Cache-Control': 'no-cache' });
}).listen(PORT, () => console.log('Docsmith website on port ' + PORT));
