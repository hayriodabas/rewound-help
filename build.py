#!/usr/bin/env python3
"""Rewound help + privacy site generator (standard library only).

Usage: python3 build.py
Reads content/<lang>.json (12 languages) and content/ui.json (app button names),
writes index.html, help.html, privacy.html, <loc>/help.html, <loc>/privacy.html,
assets/site.css and .nojekyll. Running it again gives identical output.
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
MAIL = "hayriodabas@gmail.com"
SITE = "https://hayriodabas.github.io/rewound-help/"
ISO_DATE = "2026-11-25"

# (folder, html lang, content file, UI-string language, own name)
LOCALES = [
    ("en-US", "en-US", "en", "en", "English"),
    ("de-DE", "de-DE", "de", "de", "Deutsch"),
    ("es-ES", "es-ES", "es", "es", "Español (España)"),
    ("es-MX", "es-MX", "es", "es", "Español (México)"),
    ("fr-FR", "fr-FR", "fr", "fr", "Français"),
    ("it", "it", "it", "it", "Italiano"),
    ("ja", "ja", "ja", "ja", "日本語"),
    ("ko", "ko", "ko", "ko", "한국어"),
    ("nl-NL", "nl-NL", "nl", "nl", "Nederlands"),
    ("pt-BR", "pt-BR", "pt", "pt-BR", "Português (Brasil)"),
    ("ru", "ru", "ru", "ru", "Русский"),
    ("tr", "tr", "tr", "tr", "Türkçe"),
    ("zh-Hans", "zh-Hans", "zh", "zh-Hans", "简体中文"),
]

# es-MX: same text as es with a few regional words (applied before buttons are inserted)
MX_WORDS = [("vídeo", "video"), ("Vídeo", "Video"), ("móvil", "celular"),
            ("ordenador", "computadora"), ("Uno de vosotros", "Uno de ustedes"),
            ("tu fototeca", "tu biblioteca de fotos"),
            ("Petición de valoración", "Solicitud de calificación"),
            ("pedir una valoración", "pedir una calificación"),
            ("pida que la valores", "pida que la califiques"),
            ("quién ha valorado", "quién ha calificado"),
            ("a la vez", "a la vez")]


def load(name):
    with open(os.path.join(ROOT, "content", name), encoding="utf-8") as f:
        return json.load(f)


UI = load("ui.json")["values"]
CONTENT = {}
for _f, _h, cname, _u, _n in LOCALES:
    if cname not in CONTENT:
        CONTENT[cname] = load(cname + ".json")


def fmt(text, uil, mx=False):
    """Escape text, then insert [[button]] chips and the {mail} link."""
    if mx:
        for a, b in MX_WORDS:
            text = text.replace(a, b)
    text = html.escape(text, quote=False)
    for key, val in UI[uil].items():
        text = text.replace("[[%s]]" % key, '<b class="ui">%s</b>' % html.escape(val, quote=False))
    text = text.replace("{mail}", '<a href="mailto:%s">%s</a>' % (MAIL, MAIL))
    assert "[[" not in text, text
    return text


def block(b, uil, mx):
    if isinstance(b, str):
        return "<p>%s</p>" % fmt(b, uil, mx)
    if isinstance(b, list):
        return "<ul>%s</ul>" % "".join("<li>%s</li>" % fmt(i, uil, mx) for i in b)
    if "ol" in b:
        return "<ol>%s</ol>" % "".join("<li>%s</li>" % fmt(i, uil, mx) for i in b["ol"])
    return '<div class="qa"><h3>%s</h3><p>%s</p></div>' % (fmt(b["q"], uil, mx), fmt(b["a"], uil, mx))


def sections(page, uil, mx):
    out = []
    for n, s in enumerate(page["sections"]):
        inner = "\n".join(block(b, uil, mx) for b in s["b"])
        out.append(
            '<section class="sec">\n'
            '<h2 class="seg"><span class="tape" aria-hidden="true">%03d</span>'
            '<span class="t">%s</span></h2>\n<div class="card">\n%s\n</div>\n</section>'
            % (n, fmt(s["h"], uil, mx), inner))
    return "\n".join(out)


def head(lang, title, desc, base):
    return (
        '<!doctype html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        '<title>%s</title>\n<meta name="description" content="%s">\n'
        '<link rel="icon" href="%sassets/icon.png">\n'
        '<link rel="stylesheet" href="%sassets/site.css">\n</head>\n'
        % (lang, html.escape(title), html.escape(desc, quote=True), base, base))


STRIP = '<div class="strip" aria-hidden="true"><span></span><span></span><span></span></div>'


def brand(base):
    return ('<a class="brand" href="%sindex.html"><img src="%sassets/icon.png" width="40" height="40" alt="">'
            '<span>Rewound</span></a>' % (base, base))


def page_path(folder, kind):
    return (folder + "/" if folder else "") + kind + ".html"


def lang_menu(cur_folder, kind, base, own_name, cur_html_lang):
    items = []
    for folder, hl, _c, _u, name in LOCALES:
        href = base + page_path(folder, kind)
        cur = ' aria-current="true"' if folder == cur_folder else ""
        items.append('<li><a href="%s" lang="%s" hreflang="%s"%s>%s</a></li>' % (href, hl, hl, cur, html.escape(name)))
    return ('<details class="langs"><summary lang="%s">%s</summary><ul>%s</ul></details>'
            % (cur_html_lang, html.escape(own_name), "".join(items)))


def build_page(folder, hl, cname, uil, own_name, kind):
    """kind is 'help' or 'privacy'; folder '' means the English root page."""
    c = CONTENT[cname]
    page = c[kind]
    mx = folder == "es-MX"
    base = "../" if folder else ""
    other = "privacy" if kind == "help" else "help"
    ui = c["ui"]
    menu_folder = folder or "en-US"
    nav = ('<nav class="pages" aria-label="%s"><a href="%s.html"%s>%s</a><a href="%s.html"%s>%s</a></nav>'
           % (html.escape(ui["nav"]),
              "help", ' aria-current="page"' if kind == "help" else "", html.escape(ui["help"]),
              "privacy", ' aria-current="page"' if kind == "privacy" else "", html.escape(ui["privacy"])))
    date = fmt_plain(ui["date"], mx)
    body = (
        STRIP + '\n<div class="wrap">\n<header class="top">\n' + brand(base) + "\n" + nav + "\n"
        + lang_menu(menu_folder, kind, base, own_name, hl) + '\n</header>\n<main>\n'
        '<h1>%s</h1>\n<p class="lede">%s</p>\n%s\n</main>\n'
        '<footer>\n<p>%s: <time datetime="%s">%s</time></p>\n<p><a href="%s.html">%s</a> · {mail}</p>\n</footer>\n</div>\n</body>\n</html>\n'
    ) % (fmt(page["h1"], uil, mx), fmt(page["lede"], uil, mx), sections(page, uil, mx),
         html.escape(ui["updated"]), ISO_DATE, html.escape(date), other,
         html.escape(ui[other]))
    body = body.replace("{mail}", '<a href="mailto:%s">%s</a>' % (MAIL, MAIL))
    title = fmt_plain(page["title"], mx)
    return head(hl if folder else "en", title, fmt_plain(page["desc"], mx), base) + "<body>\n" + body


def fmt_plain(t, mx):
    if mx:
        for a, b in MX_WORDS:
            t = t.replace(a, b)
    return t


def build_index():
    rows = []
    for folder, hl, cname, _u, name in LOCALES:
        ui = CONTENT[cname]["ui"]
        rows.append(
            '<li class="row"><span class="name" lang="%s">%s</span>'
            '<a href="%s" lang="%s" hreflang="%s">%s</a>'
            '<a href="%s" lang="%s" hreflang="%s">%s</a></li>'
            % (hl, html.escape(name),
               page_path(folder, "help"), hl, hl, html.escape(ui["help"]),
               page_path(folder, "privacy"), hl, hl, html.escape(ui["privacy"])))
    en = CONTENT["en"]["ui"]
    body = (
        STRIP + '\n<div class="wrap">\n<header class="top">\n' + brand("") + '\n</header>\n<main>\n'
        '<h1>Rewound: Reverse Audio</h1>\n'
        '<p class="lede">Rewound is an iPhone app that plays your voice backwards and teaches you to say it backwards; '
        'this is where its help and privacy pages live, in 13 languages.</p>\n'
        '<section class="sec">\n<h2 class="seg"><span class="tape" aria-hidden="true">000</span>'
        '<span class="t">Choose your language</span></h2>\n<div class="card">\n'
        '<ul class="langlist">\n%s\n</ul>\n</div>\n</section>\n</main>\n'
        '<footer>\n<p>%s: <time datetime="%s">%s</time></p>\n'
        '<p><a href="help.html">English help</a> · <a href="privacy.html">English privacy</a> · '
        '<a href="mailto:%s">%s</a></p>\n</footer>\n</div>\n</body>\n</html>\n'
    ) % ("\n".join(rows), html.escape(en["updated"]), ISO_DATE, html.escape(en["date"]), MAIL, MAIL)
    return head("en", "Rewound: Reverse Audio — Help and Privacy",
                "Help and privacy pages for the Rewound iPhone app, in 13 languages.", "") + "<body>\n" + body


CSS = """\
/* Rewound help site: a tape-editing bench. No scripts, no external resources. */
:root{
  --bg:#F3EEE4;--card:#FBF8F1;--ink:#1D1915;--ink2:#5C544B;
  --red:#C2391B;--oxide:#5A3E31;--guide:#E9B824;--guide-ink:#1D1915;
  --line:rgba(29,25,21,.24);--chip:rgba(90,62,49,.13);
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#15120F;--card:#211B17;--ink:#F1EADC;--ink2:#B9AFA0;
    --red:#FF7B52;--oxide:#D0AE97;
    --line:rgba(241,234,220,.26);--chip:rgba(208,174,151,.18);
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font:1.0625rem/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue","Hiragino Sans","PingFang SC","Noto Sans CJK SC","Malgun Gothic",sans-serif;
  overflow-wrap:break-word;
}
a{color:var(--red);text-underline-offset:.18em}
a:focus-visible,summary:focus-visible{outline:3px solid var(--red);outline-offset:3px;border-radius:2px}
.wrap{max-width:46rem;margin:0 auto;padding:0 16px 48px}

/* three slanted tape pieces across the top */
.strip{display:flex;gap:8px;height:18px;padding-top:0}
.strip span{display:block;height:100%;
  clip-path:polygon(10px 0,100% 0,calc(100% - 10px) 100%,0 100%)}
.strip span:nth-child(1){flex:5;background:var(--oxide)}
.strip span:nth-child(2){flex:3;background:var(--guide)}
.strip span:nth-child(3){flex:2;background:var(--red)}

.top{display:flex;flex-wrap:wrap;align-items:center;gap:12px 20px;padding:20px 0 8px}
.brand{display:inline-flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none;
  font-weight:700;font-size:1.25rem;letter-spacing:.01em}
.brand img{border-radius:9px;display:block;border:1px solid var(--line)}
.pages{display:flex;gap:6px;margin-left:auto}
.pages a{color:var(--ink);text-decoration:none;padding:4px 12px;border:1px solid var(--line);
  border-radius:3px;font-size:.95rem}
.pages a[aria-current]{background:var(--ink);color:var(--bg);border-color:var(--ink)}

.langs{flex-basis:100%;font-size:.95rem}
.langs summary{cursor:pointer;color:var(--ink2);display:inline-block;padding:2px 0;list-style:none}
.langs summary::-webkit-details-marker{display:none}
.langs summary::before{content:"";display:inline-block;width:.7em;height:.7em;margin-right:.5em;
  border:2px solid var(--oxide);border-radius:50%;vertical-align:-.05em;
  box-shadow:inset 0 0 0 2px var(--bg),inset 0 0 0 4px var(--oxide)}
.langs summary::after{content:" \\25BE"}
.langs ul{list-style:none;margin:8px 0 0;padding:10px 12px;display:flex;flex-wrap:wrap;gap:6px 16px;
  background:var(--card);border:1px solid var(--line);border-radius:4px}
.langs a[aria-current]{color:var(--ink);font-weight:700;text-decoration:none}

h1{font-size:clamp(1.65rem,6.2vw,2.3rem);line-height:1.2;margin:20px 0 8px;letter-spacing:-.01em}
.lede{color:var(--ink2);font-size:1.1rem;margin:0 0 8px}

.sec{margin-top:34px}
.seg{display:flex;align-items:center;gap:12px;font-size:1.3rem;line-height:1.3;margin:0 0 12px}
.tape{flex:none;font:700 .85rem/1 var(--mono);letter-spacing:.08em;background:var(--guide);color:var(--guide-ink);
  padding:7px 18px 7px 14px;clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%);
  transform:rotate(-2deg)}

.card{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:18px 20px;
  outline:1px solid var(--line);outline-offset:-7px;position:relative}
.card>*:first-child{margin-top:0}
.card>*:last-child{margin-bottom:0}
.card p,.card ul,.card ol{margin:0 0 12px}
.card ul,.card ol{padding-left:1.35em}
.card li{margin:0 0 6px}
.card li::marker{color:var(--oxide);font-weight:700}
.qa{margin:0 0 14px;padding-top:14px;border-top:1px dashed var(--line)}
.qa:first-child{padding-top:0;border-top:0}
.qa:last-child{margin-bottom:0}
.qa h3{font-size:1.02rem;margin:0 0 4px}
.qa p{margin:0}

.ui{font-weight:600;background:var(--chip);border-bottom:2px solid var(--oxide);padding:0 .3em;
  border-radius:2px;white-space:normal}

.langlist{list-style:none;padding:0!important;margin:0!important}
.row{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 18px;padding:9px 0;margin:0!important;
  border-top:1px dashed var(--line)}
.row:first-child{border-top:0;padding-top:0}
.row .name{flex:1 1 11rem;font-weight:700}

footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);color:var(--ink2);font-size:.92rem}
footer p{margin:0 0 4px}
@media (max-width:420px){
  .card{padding:16px 16px}
  .pages{margin-left:0}
}
"""


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    write("assets/site.css", CSS)
    write(".nojekyll", "")
    write("index.html", build_index())
    for kind in ("help", "privacy"):
        write(kind + ".html", build_page("", "en", "en", "en", "English", kind))
    for folder, hl, cname, uil, name in LOCALES:
        for kind in ("help", "privacy"):
            write(page_path(folder, kind), build_page(folder, hl, cname, uil, name, kind))
    print("done: 1 index + 2 root + %d locale pages" % (len(LOCALES) * 2))


if __name__ == "__main__":
    main()
