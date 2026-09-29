#!/usr/bin/env python3
"""ROS AMR Wiki: sayfaları üretir.

Kullanım:  python3 _src/build.py

Kaynak:   _src/pages/*.html   (her sayfanın içeriği; bölümler <section id="..."> ile)
Çıktı:    ./*.html            (ortak menü, önceki/sonraki bağlantıları ve arama dizini eklenmiş sayfalar)
          assets/search-index.js
Ortak stil ve betik: assets/style.css, assets/site.js (elle düzenlenir).
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src" / "pages"

SITE = "ROS AMR Wiki"
TAGLINE = "ROS 1 Noetic · Gazebo · Navigation"

# (dosya adı, grup, menüdeki ad, sayfa başlığı (None = ilk bölümün başlığı ya da hazır <header>))
PAGES = [
    ("index",                "Başlangıç",        "Genel bakış ve büyük resim", None),
    ("yol-haritasi",         "Başlangıç",        "Öğrenme yol haritası",       None),
    ("zihin-haritasi",       "Başlangıç",        "Zihin haritası",             None),
    ("baslarken",            "A · ROS temelleri", "Başlarken",                  "Başlarken: kurulum ve ROS'a giriş"),
    ("iletisim",             "A · ROS temelleri", "İletişim",                   "İletişim: topic, servis, action"),
    ("yapi-ve-araclar",      "A · ROS temelleri", "Yapı ve araçlar",            "Yapı ve araçlar: launch, catkin, TF"),
    ("robot-ve-simulasyon",  "B · AMR yığını",   "Robot ve simülasyon",        "Robot ve simülasyon"),
    ("harita-ve-navigasyon", "B · AMR yığını",   "Harita ve navigasyon",       "Harita ve navigasyon"),
    ("gorev-ve-docking",     "B · AMR yığını",   "Görev ve docking",           "Görev ve docking"),
    ("smach",                "B · AMR yığını",   "Durum makinesi (SMACH)",     "Durum makinesi (SMACH)"),
    ("ref-amcl-move-base",   "C · Paket referansı", "AMCL ve move_base",       "AMCL ve move_base parametreleri"),
    ("ref-costmap",          "C · Paket referansı", "costmap_2d",              "costmap_2d ve katmanları"),
    ("planlayici-parametreleri", "C · Paket referansı", "DWA ve TEB",          "DWA ve TEB parametreleri"),
    ("ref-slam-harita",      "C · Paket referansı", "gmapping ve map_server", "gmapping ve map_server parametreleri"),
    ("ref-tf-actionlib",     "C · Paket referansı", "tf ve actionlib",        "tf ve actionlib referansı"),
    ("ref-yardimci-paketler","C · Paket referansı", "twist_mux ve ira_laser_tools", "twist_mux ve ira_laser_tools parametreleri"),
    ("pratik",               "D · Pratik",       "Pratik",                     "Pratik: çalıştırma, kayıt, hata ayıklama"),
    ("referans",             "D · Pratik",       "Sözlük ve dosya düzeni",     "Sözlük ve dosya düzeni"),
    ("ornek-robot",          "E · Örnek (geliştiriliyor)", "Örnek robot",      "Örnek robot (geliştirme aşamasında)"),
]

THEME_INIT = ("try{var t=localStorage.getItem('rw-theme');"
              "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);}catch(e){}")


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def plain_text(s):
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<svg.*?</svg>", " ", s, flags=re.S)
    s = re.sub(r'<pre class="mermaid">.*?</pre>', " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def main():
    frags = {name: (SRC / f"{name}.html").read_text(encoding="utf-8") for name, *_ in PAGES}

    # bölüm id -> (sayfa, başlık)
    where, titles = {}, {}
    sections = {}  # sayfa -> [(id, başlık, düz metin)]
    for name, *_ in PAGES:
        sections[name] = []
        for m in re.finditer(r'<section id="([^"]+)">(.*?)</section>', frags[name], re.S):
            sid, body = m.group(1), m.group(2)
            h2 = re.search(r"<h2>(.*?)</h2>", body, re.S)
            title = strip_tags(h2.group(1)) if h2 else sid
            where[sid] = name
            titles[sid] = title
            sections[name].append((sid, title, plain_text(body)))

    def fix_links(content, page):
        def repl_href(m):
            sid = m.group(1)
            if sid not in where:
                print(f"  ! bilinmeyen bölüm bağlantısı: #{sid} ({page})")
                return m.group(0)
            return f'href="#{sid}"' if where[sid] == page else f'href="{where[sid]}.html#{sid}"'

        def repl_js(m):  # JS veri dizilerindeki '#bölüm' metinleri (zihin haritası)
            sid = m.group(1)
            if sid in where:
                return "'#%s'" % sid if where[sid] == page else "'%s.html#%s'" % (where[sid], sid)
            return m.group(0)

        content = re.sub(r'href="#([\w-]+)"', repl_href, content)
        content = re.sub(r"'#([a-z0-9-]+)'", repl_js, content)
        return content

    def sidebar(current):
        groups = []
        for name, group, nav, _ in PAGES:
            if not groups or groups[-1][0] != group:
                groups.append((group, []))
            groups[-1][1].append((name, nav))
        out = []
        for group, items in groups:
            lis = []
            for name, nav in items:
                cur = name == current
                cls = "pg cur" if cur else "pg"
                aria = ' aria-current="page"' if cur else ""
                li = f'<li class="{cls}"><a href="{name}.html"{aria}>{html.escape(nav)}</a>'
                if cur and len(sections[name]) > 1:
                    li += '<ul class="sub">' + "".join(
                        f'<li><a href="#{sid}">{html.escape(t)}</a></li>' for sid, t, _ in sections[name]
                    ) + "</ul>"
                lis.append(li + "</li>")
            out.append(f'<div class="grp"><h2>{html.escape(group)}</h2><ul>{"".join(lis)}</ul></div>')
        return (
            '<aside class="side"><details id="navd" open>'
            f"<summary>{SITE}</summary>"
            f'<p class="brand"><a href="index.html">{SITE}</a><small>{TAGLINE}</small></p>'
            '<div class="searchbox"><input class="find" id="find" type="search" placeholder="Sitede ara…  ( / )" '
            'aria-label="Sitede ara" autocomplete="off"><ul class="results" id="results" hidden></ul></div>'
            f'<nav id="nav" aria-label="Sayfalar">{"".join(out)}</nav>'
            '<p class="foot">Hedef sürüm: ROS 1 Noetic (Ubuntu 20.04)'
            '<br><button type="button" class="themebtn" id="themebtn">Tema: Sistem</button></p>'
            "</details></aside>"
        )

    index_records = []
    for i, (name, group, nav, h1) in enumerate(PAGES):
        content = frags[name]
        if not content.lstrip().startswith("<header"):
            first_h2 = re.search(r"<h2>(.*?)</h2>", content, re.S)
            if h1 is None and first_h2:
                # tek bölümlü sayfa: bölüm başlığı sayfa başlığı olur
                page_title = strip_tags(first_h2.group(1))
                content = content.replace(first_h2.group(0), f"<h1>{first_h2.group(1)}</h1>", 1)
                content = content.replace(
                    "<h1>", f'<p class="eyebrow">{html.escape(group)}</p>\n<h1>', 1)
            else:
                page_title = h1
                head = (f'<header class="pagehead"><p class="eyebrow">{html.escape(group)}</p>'
                        f"<h1>{html.escape(h1)}</h1></header>\n")
                content = head + content
        else:
            page_title = SITE
        content = fix_links(content, name)

        # önceki / sonraki
        pager = ""
        prev_p = PAGES[i - 1] if i > 0 else None
        next_p = PAGES[i + 1] if i < len(PAGES) - 1 else None
        parts = []
        if prev_p:
            parts.append(f'<a class="prev" href="{prev_p[0]}.html"><small>← Önceki</small>{html.escape(prev_p[2])}</a>')
        if next_p:
            parts.append(f'<a class="next" href="{next_p[0]}.html"><small>Sonraki →</small>{html.escape(next_p[2])}</a>')
        if parts:
            pager = f'<nav class="pager" aria-label="Sayfa gezintisi">{"".join(parts)}</nav>'
        # sayfa altı notu (index) pager'dan önce kalsın
        doc = content + "\n" + pager

        desc = ""
        m = re.search(r"<p[^>]*>(.*?)</p>", re.sub(r'<p class="eyebrow">.*?</p>', "", content, flags=re.S), re.S)
        if m:
            desc = strip_tags(m.group(1))[:170]
        title_tag = SITE if name == "index" else f"{page_title} · {SITE}"
        mermaid = ('<script defer src="assets/mermaid.min.js"></script>\n' if 'class="mermaid"' in content else "")
        page = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title_tag)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="icon" href="data:,">
<script>{THEME_INIT}</script>
<link rel="stylesheet" href="assets/fonts.css">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="shell">
{sidebar(name)}
<main>
<div class="doc">
{doc}
</div>
</main>
</div>
<script defer src="assets/search-index.js"></script>
{mermaid}<script defer src="assets/site.js"></script>
</body>
</html>
"""
        (ROOT / f"{name}.html").write_text(page, encoding="utf-8")

        for sid, t, text in sections[name]:
            index_records.append({"p": f"{name}.html", "id": sid, "t": t, "pg": nav, "x": text[:120000]})

    (ROOT / "assets" / "search-index.js").write_text(
        "window.SEARCH_INDEX=" + json.dumps(index_records, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"{len(PAGES)} sayfa, {len(index_records)} bölüm dizine alındı.")


if __name__ == "__main__":
    main()
