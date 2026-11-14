#!/usr/bin/env python3
"""Builds public/index.html from the Design canvas file (Main.dc.html).

Renders <sc-for>, <sc-if> and {{holes}} with the component's data (vals.json,
extracted with tools/extract.js), swaps blob image URLs for local assets, fills the
contact / link placeholders and wires the trial form to the n8n webhook.
"""
import html, json, re, sys

SRC, VALS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(SRC, encoding='utf-8').read()
vals = json.load(open(VALS, encoding='utf-8'))
body = src.split('<x-dc>', 1)[1].split('</x-dc>', 1)[0]
helmet = re.search(r'<helmet>([\s\S]*?)</helmet>', body).group(1)
body = re.sub(r'<helmet>[\s\S]*?</helmet>', '', body)

# the two form states: keep the form, render the thank-you hidden (JS toggles it)
vals['sent'] = True
vals['notSent'] = True
vals['firstName'] = ''
vals['email'] = ''


def lookup(path, scope):
    path = path.strip()
    if path in ('true', 'false'):
        return path == 'true'
    cur = scope
    for part in path.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return ''
    return cur


TOKEN = re.compile(r'<(sc-for|sc-if)\b([^>]*)>|</(sc-for|sc-if)>')


def parse(s, i=0, close=None):
    """-> (list of nodes, index). node = str | (tag, attrs, children)"""
    out = []
    while True:
        m = TOKEN.search(s, i)
        if not m:
            out.append(s[i:])
            return out, len(s)
        out.append(s[i:m.start()])
        if m.group(3):  # closing
            return out, m.end()
        kids, j = parse(s, m.end(), m.group(1))
        out.append((m.group(1), m.group(2), kids))
        i = j


def attr(a, name):
    m = re.search(name + r'="([^"]*)"', a)
    return m.group(1) if m else ''


def hole_path(v):
    m = re.match(r'\s*\{\{\s*([^}]+?)\s*\}\}\s*$', v)
    return m.group(1) if m else v


def fill(text, scope):
    def rep(m):
        v = lookup(m.group(1), scope)
        return html.escape(str(v), quote=True) if not isinstance(v, bool) else ''
    return re.sub(r'\{\{\s*([^}]+?)\s*\}\}', rep, text)


def render(nodes, scope):
    out = []
    for n in nodes:
        if isinstance(n, str):
            out.append(fill(n, scope))
            continue
        tag, a, kids = n
        if tag == 'sc-for':
            lst = lookup(hole_path(attr(a, 'list')), scope) or []
            name = attr(a, 'as')
            for idx, item in enumerate(lst):
                sc = dict(scope)
                sc[name] = item
                sc['$index'] = idx
                out.append(render(kids, sc))
        else:
            if lookup(hole_path(attr(a, 'value')), scope):
                out.append(render(kids, scope))
    return ''.join(out)


nodes, _ = parse(body)
page = render(nodes, vals)

# style strings bound into style="" came through html-escaped once: undo &#x27; etc. inside style attrs only
page = re.sub(r'style="([^"]*)"', lambda m: 'style="' + html.unescape(m.group(1)).replace('"', "'") + '"', page)

# events / form state
page = page.replace(' onSubmit=""', ' id="trial-form" novalidate').replace(' onClick=""', ' id="trial-again"')
page = page.replace('<div role="status" style="', '<div role="status" id="trial-thanks" hidden style="', 1)
page = page.replace('<h3 style="margin: 0; font-size: 22px">Thanks, ! Check your inbox.</h3>',
                    '<h3 style="margin: 0; font-size: 22px">Thanks<span id="trial-name"></span>! Check your inbox.</h3>')
page = page.replace('are on their way to . They stay valid for 7 days.', 'are on their way to <b id="trial-email"></b>.')

# assets
BLOBS = {
    '/_blob/49b0177424da6cc7efd92a035a485dc9': '/assets/docsmith-logo.svg',
    '/_blob/d09a2a80a225256c84c8584f2892bf05': '/assets/designer.jpg',
    '/_blob/01c97470f174e7d5a6dd224e53421c85': '/assets/invoice.jpg',
    '/_blob/57d9d608d7558150793f3da1f652948b': '/assets/payslip.jpg',
}
for k, v in BLOBS.items():
    page = page.replace(k, v)
page = page.replace('<img src="/assets/designer.jpg"', '<img src="/assets/designer.jpg" width="2160" height="1154" fetchpriority="high"')
page = page.replace('<img src="/assets/invoice.jpg"', '<img src="/assets/invoice.jpg" loading="lazy"')
page = page.replace('<img src="/assets/payslip.jpg"', '<img src="/assets/payslip.jpg" loading="lazy"')

# placeholders
GUIDE = 'https://drive.google.com/file/d/1soMgrlz3duRIfWHdyO6UpsrHzfJPc-TG/view'
DOWNLOADS = 'https://drive.google.com/drive/folders/1zkcE62UhsYtb12w--aUBu2SkMbH20Jx5'
EMAIL = 'bgowryshangar@gmail.com'
page = page.replace('[sales@yourdomain]', EMAIL).replace('[support@yourdomain]', EMAIL)
page = page.replace('href="[PRIVACY URL]"', 'href="/privacy"')
page = page.replace('href="[DOCS URL]"', 'href="' + GUIDE + '" target="_blank" rel="noopener"')
page = re.sub(r'\s*<a href="\[PORTAL URL\]"[^>]*>[^<]*</a>', '', page)   # no public downloads link: files go out by e-mail after the trial form
# live demo: the in-browser designer at /demo
page = page.replace('href="[DEMO URL]"', 'href="/demo"')
page = re.sub(r'\s*<a href="\[TERMS URL\]"[^>]*>[^<]*</a>', '', page)
page = re.sub(r'\s*<a href="\[LINKEDIN URL\]"[^>]*>LinkedIn</a>', '', page)
page = re.sub(r'\s*<a href="https://wa.me/\[YOUR NUMBER\]"[^>]*>WhatsApp \[\+94 XX XXX XXXX\]</a>', '', page)
page = page.replace('Prefer to talk first? WhatsApp <a href="https://wa.me/[YOUR NUMBER]">[+94 XX XXX XXXX]</a> or e-mail',
                    'Prefer to talk first? E-mail')
# purchase buttons -> /buy
page = re.sub(r'<a href="#trial"([^>]*)>Buy Pro</a>', r'<a href="/buy?plan=pro"\1>Buy Pro</a>', page)
page = re.sub(r'<a href="#contact"([^>]*)>Contact sales</a>', r'<a href="/buy?plan=enterprise"\1>Contact sales</a>', page)
page = page.replace('[Company name], [City], Sri Lanka', 'Sri Lanka')
page = page.replace('© 2026 [Company name].', '© 2026 Docsmith.')
page = page.replace('Not there in 5 minutes? Look in spam or WhatsApp us.', 'Not there in 5 minutes? Look in your spam folder or e-mail us.')
left = re.findall(r'\[[A-Z][A-Za-z +#0-9@./-]*\]', page)
if left:
    print('placeholders left:', sorted(set(left)))

head = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Docsmith – visual PDF, Word and Excel report designer for Oracle APEX</title>
<meta name="description" content="Design pixel-perfect invoices, payslips, letters and forms visually inside Oracle APEX. PDF, Word and Excel output, Tamil and Sinhala support, runs on your own servers. 30-day free trial.">
<link rel="canonical" href="/">
<meta property="og:title" content="Docsmith – report designer for Oracle APEX">
<meta property="og:description" content="Pixel-perfect PDF, Word and Excel documents, designed visually inside APEX. 30-day free trial.">
<meta property="og:image" content="/assets/designer.jpg">
<meta property="og:type" content="website">
<link rel="icon" type="image/svg+xml" href="/assets/docsmith-logo.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/app-icon-32.png">
<link rel="apple-touch-icon" href="/assets/app-icon-192.png">
''' + helmet.strip() + '''
<style>html{scroll-behavior:smooth;scroll-padding-top:80px}img{max-width:100%}[hidden]{display:none!important}@media (max-width:720px){header nav>div{display:none!important}header nav>a:last-child{margin-left:auto}}</style>
</head>
<body>
'''

script = '''
<script>
(function () {
  var WEBHOOK = 'https://n8n.srv834342.hstgr.cloud/webhook-test/docsmith-trial';   // TEST url: change to /webhook/ after publishing the workflow
  var form = document.getElementById('trial-form');
  var thanks = document.getElementById('trial-thanks');
  if (!form) return;
  var btn = form.querySelector('button[type=submit]');
  var err = document.createElement('p');
  err.setAttribute('role', 'alert');
  err.style.cssText = 'grid-column:1/-1;margin:0;color:#b42318;font-size:14px';
  form.appendChild(err);
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    err.textContent = '';
    if (!form.reportValidity()) return;
    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = v; });
    btn.disabled = true; btn.textContent = 'Sending…';
    fetch(WEBHOOK, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || j.ok === false) throw new Error(j.error || 'Request failed'); return j; }); })
      .then(function () {
        document.getElementById('trial-name').textContent = data.name ? ', ' + String(data.name).split(' ')[0] : '';
        document.getElementById('trial-email').textContent = data.email;
        form.hidden = true; thanks.hidden = false; thanks.scrollIntoView({ block: 'center' });
      })
      .catch(function (x) { err.textContent = (x && x.message && x.message !== 'Request failed' ? x.message + ' ' : '') + 'Sorry, that did not go through. Please try again or e-mail ''' + EMAIL + '''.'; })
      .then(function () { btn.disabled = false; btn.textContent = 'Send me the download links'; });
  });
  document.getElementById('trial-again').addEventListener('click', function () { form.reset(); thanks.hidden = true; form.hidden = false; });
})();
</script>
</body>
</html>
'''
open(OUT, 'w', encoding='utf-8').write(head + page.strip() + script)
print('wrote', OUT, len(head + page + script), 'bytes')
