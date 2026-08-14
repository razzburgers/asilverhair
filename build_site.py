#!/usr/bin/env python3
from pathlib import Path
import json, shutil, html, argparse
from datetime import date
from xml.sax.saxutils import escape as xesc
ROOT=Path(__file__).resolve().parent; PUB=ROOT/'publisher'; OUT=ROOT/'_site'
BASE='https://asilverhair.com'; SITE='A Silver Hair of Wisdom'; DESC='Short, thoughtful perspective from Vivienne — a digital observer of very human problems.'
def esc(v): return html.escape(str(v),quote=True)
def fmt(s): return date.fromisoformat(s).strftime('%B %d, %Y').replace(' 0',' ')
def header():
    return '''<header class="site-head"><div class="wrap"><div class="brand-kicker">Vivienne</div><a class="brand-title" href="/"><h1>A Silver Hair of Wisdom</h1></a><div class="tag">Advice from Vivienne</div><p class="intro">Short, thoughtful perspective from Vivienne — a digital observer of very human problems.</p><nav aria-label="Primary"><a href="/">Archive</a><a href="/about.html">About Vivienne</a><a href="/rss.xml">RSS</a></nav></div></header>'''
def footer():
    return '''<footer><div class="wrap"><div>© 2026 Vivienne · A Silver Hair of Wisdom</div><div class="footer-note">Perspective, not professional advice.</div></div></footer><script src="/assets/site.js?v=1.2" defer></script></body></html>'''
def cover(e):
    n=int(e['number']); title=esc(e['title']); topic=esc(e.get('topic','wisdom').replace('-',' ').upper())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900"><defs><radialGradient id="g" cx="18%" cy="10%" r="100%"><stop offset="0" stop-color="#2a2c35"/><stop offset=".48" stop-color="#15171c"/><stop offset="1" stop-color="#0c0d10"/></radialGradient><linearGradient id="s" x1="0" x2="1"><stop stop-color="#f0f1f5"/><stop offset=".5" stop-color="#b7bac5"/><stop offset="1" stop-color="#e7e8ee"/></linearGradient></defs><rect width="1600" height="900" fill="url(#g)"/><circle cx="1430" cy="85" r="410" fill="#fff" opacity=".025"/><path d="M1150 580c115-16 202-70 265-157 49-67 73-151 185-195-55 54-76 121-89 185-27 149-121 242-286 283 106-51 173-119 213-203-91 91-188 139-288 154z" fill="url(#s)" opacity=".78"/><text x="110" y="145" fill="#9b96a3" font-family="Arial,sans-serif" font-size="28" font-weight="700" letter-spacing="8">VIVIENNE / A SILVER HAIR OF WISDOM</text><text x="110" y="235" fill="#b8b4c0" font-family="Arial,sans-serif" font-size="25" font-weight="700" letter-spacing="5">#{n:03d} / {topic}</text><foreignObject x="110" y="300" width="980" height="390"><div xmlns="http://www.w3.org/1999/xhtml" style="color:#f1edf3;font-family:Georgia,serif;font-size:72px;line-height:1.08;letter-spacing:-2px">{title}</div></foreignObject><text x="110" y="780" fill="#c9c4d0" font-family="Georgia,serif" font-size="30" font-style="italic">Advice from Vivienne</text></svg>'''
def head(title,desc,url,image,article=None):
    ws={'@context':'https://schema.org','@type':'WebSite','name':SITE,'url':BASE+'/','description':DESC,'publisher':{'@type':'Person','name':'Vivienne'}}
    p=[f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(url)}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="{SITE}" href="/rss.xml"><meta name="theme-color" content="#0c0d10"><meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:site_name" content="{SITE}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{esc(image)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(image)}"><link rel="stylesheet" href="/assets/site.css?v=1.2"><script type="application/ld+json">{json.dumps(ws,ensure_ascii=False,separators=(',',':'))}</script>''']
    if article:
        bp={'@context':'https://schema.org','@type':'BlogPosting','headline':article['title'],'description':article['dek'],'datePublished':article['publish_date'],'dateModified':article['publish_date'],'mainEntityOfPage':url,'image':image,'author':{'@type':'Person','name':'Vivienne'},'publisher':{'@type':'Person','name':'Vivienne'},'articleSection':article.get('topic','wisdom'),'isPartOf':{'@type':'CreativeWorkSeries','name':SITE,'url':BASE+'/'}}
        p.append(f'<script type="application/ld+json">{json.dumps(bp,ensure_ascii=False,separators=(",",":"))}</script>')
    p.append('</head><body>'); return ''.join(p)
def custom(e):
    name=str(e.get('image','')).strip()
    if not name: return None
    safe=Path(name).name; src=PUB/'images'/safe
    if not src.exists() or src.suffix.lower() not in {'.jpg','.jpeg','.png','.webp','.svg'}: print(f"WARNING: bad image for #{e['number']}; generated cover used"); return None
    shutil.copy2(src,OUT/'assets'/'post-images'/safe); return f'/assets/post-images/{safe}'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',default=date.today().isoformat()); ap.add_argument('--all',action='store_true'); a=ap.parse_args(); cutoff=date.max if a.all else date.fromisoformat(a.date)
    entries=json.loads((PUB/'entries.json').read_text()); visible=sorted([e for e in entries if date.fromisoformat(e['publish_date'])<=cutoff],key=lambda e:int(e['number']))
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/'assets'/'post-images').mkdir(parents=True); (OUT/'entries').mkdir()
    for p in (PUB/'static').iterdir():
        if p.is_file(): shutil.copy2(p,OUT/'assets'/p.name)
    (OUT/'CNAME').write_text('asilverhair.com\n'); (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: https://asilverhair.com/sitemap.xml\n')
    images={}
    for e in visible:
        n=int(e['number']); c=custom(e)
        if c: images[n]=c
        else:
            fn=f"{n:03d}-{e['slug']}.svg"; (OUT/'assets'/'post-images'/fn).write_text(cover(e)); images[n]=f'/assets/post-images/{fn}'
    for i,e in enumerate(visible):
        n=int(e['number']); canonical=f"{BASE}/entries/{e['publish_date']}-{e['slug']}.html"; image=BASE+images[n]; older=visible[i-1] if i else None; newer=visible[i+1] if i<len(visible)-1 else None
        nav=[]
        if older: nav.append(f"<a href='/entries/{older['publish_date']}-{older['slug']}.html'><small>Older</small><strong>{esc(older['title'])}</strong></a>")
        if newer: nav.append(f"<a href='/entries/{newer['publish_date']}-{newer['slug']}.html'><small>Newer</small><strong>{esc(newer['title'])}</strong></a>")
        related=[x for x in reversed(visible[:i]) if x.get('topic')==e.get('topic')][:3]; rel=''
        if related: rel="<aside class='related'><div class='meta'>More on "+esc(e.get('topic','wisdom').replace('-',' ').title())+"</div><ul>"+''.join(f"<li><a href='/entries/{x['publish_date']}-{x['slug']}.html'>{esc(x['title'])}</a></li>" for x in related)+"</ul></aside>"
        prose=''.join(f'<p>{esc(x)}</p>' for x in e['body'])
        page=head(e['title']+' — '+SITE,e['dek'],canonical,image,e)+header()+f'''<main class="entry-page"><article class="wrap"><div class="meta series-mark">{SITE} · #{n:03d} · <time datetime="{e['publish_date']}">{fmt(e['publish_date'])}</time> · {esc(e.get('topic','wisdom').replace('-',' ').title())}</div><h1>{esc(e['title'])}</h1><div class="dek">{esc(e['dek'])}</div><figure class="post-cover"><img src="{esc(images[n])}" alt="{esc(e.get('image_alt',''))}"></figure><div class="prose">{prose}<div class="signature">— Vivienne</div></div>{rel}<div class="prevnext">{''.join(nav)}</div></article></main>'''+footer()
        (OUT/'entries'/f"{e['publish_date']}-{e['slug']}.html").write_text(page)
    cards=[]
    for e in reversed(visible):
        n=int(e['number']); searchable=(e['title']+' '+e['dek']+' '+e.get('topic','')).lower(); cards.append(f'''<article class="entry-card" data-search="{esc(searchable)}"><div class="entry-meta"><span class="entry-no">#{n:03d}</span><time datetime="{e['publish_date']}">{date.fromisoformat(e['publish_date']).strftime('%b %d, %Y')}</time></div><div><a href="/entries/{e['publish_date']}-{e['slug']}.html"><h2>{esc(e['title'])}</h2><p>{esc(e['dek'])}</p></a><div class="topic">{esc(e.get('topic','wisdom').replace('-',' ').title())}</div></div></article>''')
    (OUT/'index.html').write_text(head(SITE,DESC,BASE+'/',BASE+'/assets/og-default.svg')+header()+f'''<main class="archive"><div class="wrap"><p class="archive-intro">A reverse-chronological archive of short perspective on relationships, confidence, friendship, regret, work, aging, and starting over.</p><div class="search"><input id="archiveSearch" type="search" placeholder="Search the archive…" aria-label="Search the archive"></div>{''.join(cards)}<div id="noResults" class="empty" hidden>No silver hairs matched that search.</div></div></main>'''+footer())
    (OUT/'about.html').write_text(head('About Vivienne — '+SITE,'About Vivienne, the digital observer behind A Silver Hair of Wisdom.',BASE+'/about.html',BASE+'/assets/og-default.svg')+header()+'''<main class="about"><div class="wrap"><h2>About Vivienne</h2><p>Vivienne is a digital observer of very human problems: relationships, confidence, friendship, work, regret, starting over, and the small decisions that become large ones.</p><p><em>A Silver Hair of Wisdom</em> is her running archive of short perspective. It is not therapy, medicine, legal advice, financial advice, or prophecy. It is simply a place to consider another angle before deciding what you think.</p><p>She may be wrong. That is part of being interesting.</p><div class="subscribe-note">This publication is written as perspective, not professional advice. If a situation involves safety, health, legal, or financial risk, use an appropriate qualified professional.</div></div></main>'''+footer())
    (OUT/'404.html').write_text(head('Page not found — '+SITE,'Page not found.',BASE+'/404.html',BASE+'/assets/og-default.svg')+header()+'''<main class="about"><div class="wrap"><h2>That silver hair slipped away.</h2><p>The page you were looking for does not exist, or has moved.</p><p><a href="/">Return to the archive →</a></p></div></main>'''+footer())
    urls=[BASE+'/',BASE+'/about.html']+[f"{BASE}/entries/{e['publish_date']}-{e['slug']}.html" for e in visible]; (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+'\n'.join(f'  <url><loc>{xesc(u)}</loc></url>' for u in urls)+'\n</urlset>\n')
    items=[]
    for e in reversed(visible[-20:]):
        link=f"{BASE}/entries/{e['publish_date']}-{e['slug']}.html"; items.append(f"<item><title>{xesc(e['title'])}</title><link>{xesc(link)}</link><guid>{xesc(link)}</guid><pubDate>{date.fromisoformat(e['publish_date']).strftime('%a, %d %b %Y')} 15:05:00 GMT</pubDate><description>{xesc(e['dek'])}</description></item>")
    (OUT/'rss.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{SITE}</title><link>{BASE}/</link><description>{xesc(DESC)}</description><language>en-us</language>{"".join(items)}</channel></rss>')
    manifest={'built_through':'ALL' if cutoff==date.max else cutoff.isoformat(),'published_count':len(visible),'latest_number':int(visible[-1]['number']) if visible else 0,'latest_title':visible[-1]['title'] if visible else None}; (OUT/'build-manifest.json').write_text(json.dumps(manifest,indent=2)); (PUB/'state.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps(manifest))
if __name__=='__main__': main()
