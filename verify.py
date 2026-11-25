#!/usr/bin/env python3
"""Checks the generated site (standard library only). Run after build.py."""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))
XC = "/Users/hayriodabas/Depo/Projeler/Swift/rewound/Sources/Resources/Localizable.xcstrings"

LOCS = {  # folder -> (expected lang, xcstrings language)
    "en-US": ("en-US", "en"), "de-DE": ("de-DE", "de"), "es-ES": ("es-ES", "es"), "es-MX": ("es-MX", "es"),
    "fr-FR": ("fr-FR", "fr"), "it": ("it", "it"), "ja": ("ja", "ja"), "ko": ("ko", "ko"),
    "nl-NL": ("nl-NL", "nl"), "pt-BR": ("pt-BR", "pt-BR"), "ru": ("ru", "ru"), "tr": ("tr", "tr"),
    "zh-Hans": ("zh-Hans", "zh-Hans"),
}
BANNED = ["tiktok", "instagram", "youtube", "reels", "trending", "reverse voice", "funny voice"]
CURRENCY = re.compile(r"[$€¥₺£]|\d\s?(?:TL|USD|EUR|TRY|JPY|CNY|RUB|₽|円|元|원|руб)", re.I)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ui, self.text, self._ui, self.title, self._t = [], [], [], False, "", False
        self.lang = None
        self.meta = {}
        self.script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "meta":
            self.meta[a.get("name") or ("charset" if "charset" in a else "")] = a.get("content", "1")
        if tag in ("a", "link") and a.get("href"):
            self.links.append(a["href"])
        if tag in ("img", "script") and a.get("src"):
            self.links.append(a["src"])
        if tag == "script":
            self.script = True
        if tag == "title":
            self._t = True
        if tag == "b" and a.get("class") == "ui":
            self._ui = True
            self.ui.append("")

    def handle_endtag(self, tag):
        if tag == "b":
            self._ui = False
        if tag == "title":
            self._t = False

    def handle_data(self, d):
        self.text.append(d)
        if self._ui:
            self.ui[-1] += d
        if self._t:
            self.title += d


def main():
    pages = []
    for dp, _, fs in os.walk(ROOT):
        if ".git" in dp or "/content" in dp:
            continue
        for f in fs:
            if f.endswith(".html"):
                pages.append(os.path.relpath(os.path.join(dp, f), ROOT))
    pages.sort()
    errors = 0
    print("HTML count:", len(pages))
    for rel in pages:
        p = P()
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        p.feed(src)
        folder = os.path.dirname(rel)
        exp = "en" if folder == "" else LOCS[folder][0]
        txt = "".join(p.text)
        probs = []
        if p.lang != exp:
            probs.append("lang %r != %r" % (p.lang, exp))
        if "charset" not in p.meta or "viewport" not in p.meta:
            probs.append("meta charset/viewport")
        if not p.title.strip():
            probs.append("empty title")
        if "mailto:hayriodabas@gmail.com" not in src:
            probs.append("mailto")
        if not re.search(r"(?<!\d)25(?!\d)", txt) or "2026" not in txt:
            probs.append("date 25 / 2026")
        if p.script or "<script" in src or "http://" in src or "https://" in src:
            probs.append("script or external reference")
        for l in p.links:
            if re.match(r"^(mailto:|https?:|#)", l):
                continue
            target = os.path.normpath(os.path.join(ROOT, folder, l.split("#")[0]))
            if not os.path.isfile(target):
                probs.append("broken link " + l)
        if CURRENCY.search(src):
            probs.append("currency/price: " + CURRENCY.search(src).group(0))
        low = src.lower()
        for w in BANNED:
            if w in low:
                probs.append("banned word " + w)
        if probs:
            errors += 1
            print("FAIL", rel, probs)
    print("pages with problems:", errors)

    # button names against the app's own strings
    d = json.load(open(XC, encoding="utf-8"))["strings"]
    keys = {"Copy it": "game.copyIt", "Slow": "splice.slow", "Save round": "game.save",
            "Delete all recordings": "tape.deleteAll", "Restore Purchase": "backmask.restore",
            "Pass the phone": "game.mode.party"}
    allvals = {}
    mism = 0
    print("\nButton names (help page vs Localizable.xcstrings):")
    for folder, (hl, xl) in LOCS.items():
        p = P()
        p.feed(open(os.path.join(ROOT, folder, "help.html"), encoding="utf-8").read())
        vals = {k: d[k]["localizations"][xl]["stringUnit"]["value"].replace("%lld", "N") for k in d}
        known = set(vals.values())
        row = []
        for en, k in keys.items():
            v = vals[k]
            ok = v in p.ui
            mism += not ok
            row.append("%s %s" % ("OK" if ok else "MISSING", v))
        unknown = sorted({u for u in p.ui if u not in known})
        mism += len(unknown)
        print(" %-8s %s%s" % (folder, " | ".join(row), ("  UNKNOWN: %s" % unknown) if unknown else ""))
        print("          chips on page: %d, all found in xcstrings: %s" % (len(p.ui), not unknown))
    print("button mismatches:", mism)
    sys.exit(1 if errors or mism else 0)


if __name__ == "__main__":
    main()
