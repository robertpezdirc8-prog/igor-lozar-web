#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ograje Lozar — preverjanje pripravljenosti strani.

Vzame sam nazaj in izpise kontrolne rezultate. Izstopna koda je 0 samo,
ce vsi prehodi. Vsako kontrolo je mogoce namenoma pokvariti (mutacijski
test), da se vidi, ali res zazna napako ali samo potrjuje.

Uporaba:  python scripts/preveri.py [--verbose]
"""

import base64
import hashlib
import json
import os
import re
import sys
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_ORIGIN = "https://robertpezdirc8-prog.github.io/igor-lozar-web"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# Elementi, ki samodejno zaprejo predhodnika (npr. <li> znotraj <ul>)
AUTO_CLOSE = {
    "li": {"li"}, "p": {"p"}, "td": {"td", "th"}, "th": {"td", "th"},
    "tr": {"tr", "td", "th"}, "dd": {"dd", "dt"}, "dt": {"dd", "dt"},
    "option": {"option"}, "thead": {"thead"}, "tbody": {"thead", "tbody"},
}

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    return ok


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- 1.oznake
class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        for closer in AUTO_CLOSE.get(tag, ()):
            if self.stack and self.stack[-1][0] == closer:
                self.stack.pop()
        self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"zaprta oznaka <{tag}> brez ujemace odpiralne na {self.getpos()[0]}")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        open_tags = [t for t, _ in self.stack]
        if tag in open_tags:
            while self.stack and self.stack[-1][0] != tag:
                t, pos = self.stack.pop()
                self.errors.append(f"nezaprla oznaka <{t}> (odprta na {pos[0]}) preklicana z </{tag}> na {self.getpos()[0]}")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"osamljena zapiralna oznaka </{tag}> na {self.getpos()[0]}")

    def close(self):
        super().close()
        for t, pos in self.stack:
            self.errors.append(f"nezaprta oznaka <{t}> odprta na {pos[0]}")


def check_markup():
    for page in ("index.html", "zasebnost.html", "404.html"):
        p = Balance()
        p.feed(read(page))
        p.close()
        check(f"Uravnotezenost oznak v {page}", not p.errors, "; ".join(p.errors[:4]))


# ---------------------------------------------------------------- 2.slike
def check_pictures(html):
    missing_attr, not_wrapped, missing_file, bad_alt = [], [], [], []
    for m in re.finditer(r"<img\b[^>]*>", html):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src:
            continue
        src = src.group(1)
        if src.startswith("data:"):
            continue
        attrs = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', tag))
        for need in ("alt", "width", "height", "loading", "decoding"):
            if need not in attrs:
                missing_attr.append(f"{src}: brez {need}")
        if not attrs.get("alt", "").strip():
            bad_alt.append(src)
        if re.fullmatch(r"[\w.-]+\.(jpg|png|webp|avif)", attrs.get("alt", ""), re.I):
            bad_alt.append(f"{src}: alt je ime datoteke")
        # ozadje slike mora biti v <picture> z avif in webp viri
        before = html[max(0, m.start() - 400):m.start()]
        if "<picture" not in before or before.rfind("</picture>") > before.rfind("<picture"):
            not_wrapped.append(src)
        else:
            for ext in ("avif", "webp"):
                want = re.sub(r"\.(jpg|png)$", "." + ext, src)
                if want not in before:
                    not_wrapped.append(f"{src}: manjka {ext} source")
                elif not os.path.isfile(os.path.join(ROOT, want)):
                    missing_file.append(want)
        if not src.startswith(("http", "data:", "/")) and not os.path.isfile(os.path.join(ROOT, src)):
            missing_file.append(src)
    check("Vse <img> imajo alt/width/height/loading/decoding", not missing_attr, "; ".join(missing_attr[:4]))
    check("Vse <img> so v <picture> z AVIF in WebP", not not_wrapped, "; ".join(not_wrapped[:4]))
    check("Vse referencirane datoteke obstajajo", not missing_file, "; ".join(missing_file[:4]))
    check("Noben alt ni prazen ali ime datoteke", not bad_alt, "; ".join(bad_alt[:4]))


def check_dimensions(html):
    from PIL import Image
    bad = []
    for m in re.finditer(r'<img\b[^>]*src="([^"?#]+)"[^>]*>', html):
        src = m.group(1)
        if src.startswith(("http", "data:")):
            continue
        path = os.path.join(ROOT, src.lstrip("/").replace("igor-lozar-web/", ""))
        if not os.path.isfile(path):
            continue
        tag = m.group(0)
        w = re.search(r'width="(\d+)"', tag)
        h = re.search(r'height="(\d+)"', tag)
        if not (w and h):
            continue
        with Image.open(path) as im:
            real = im.size
        if (int(w.group(1)), int(h.group(1))) != real:
            bad.append(f"{src}: zapisano {w.group(1)}x{h.group(1)}, resnice {real[0]}x{real[1]}")
    check("Dimenzije v HTML ustrezajo slikam (brez CLS)", not bad, "; ".join(bad[:3]))


def check_weight():
    budget = {"img/hero-realizacije.avif": 60_000, "img/hero-realizacije.webp": 140_000,
              "img/hero-realizacije.jpg": 220_000}
    over = []
    for f, lim in budget.items():
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p):
            over.append(f"{f}: manjka")
        elif os.path.getsize(p) > lim:
            over.append(f"{f}: {os.path.getsize(p)} B > {lim} B")
    check("LCP slika znotraj prorasuna", not over, "; ".join(over))


# ---------------------------------------------------------------- 3.povezave
def check_links(html):
    anchors = set(re.findall(r'\bid="([^"]+)"', html))
    broken, insecure = [], []
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith("#"):
            if href[1:] not in anchors:
                broken.append(href)
        elif href.startswith("http://"):
            insecure.append(href)
        elif href.startswith(SITE_ORIGIN):
            rel = href[len(SITE_ORIGIN):].split("#")[0].lstrip("/")
            if rel and not os.path.isfile(os.path.join(ROOT, rel)):
                broken.append(href)
        elif not href.startswith(("mailto:", "tel:", "https://", "/")):
            target = href.split("#")[0]
            if target and not os.path.isfile(os.path.join(ROOT, target)):
                broken.append(href)
    check("Vse znotrajstranske sidrne povezave imajo cilj", not broken, "; ".join(broken[:4]))
    check("Nobena povezava ni navadni HTTP", not insecure, "; ".join(insecure[:4]))


# ---------------------------------------------------------------- 4.JSON-LD
def check_jsonld(html):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not check("JSON-LD blok obstaja", len(blocks) == 1, f"najdenih {len(blocks)}"):
        return
    try:
        data = json.loads(blocks[0])
    except Exception as e:
        check("JSON-LD je veljaven JSON", False, str(e))
        return
    check("JSON-LD je veljaven JSON", True)
    expect = {
        "vatID": "SI22822577",
        "taxID": "22822577",
        "foundingDate": "1996-06-04",
        "telephone": "+38641276195",
        "email": "lesne.storitve@gmail.com",
    }
    bad = [f"{k}={data.get(k)}" for k, v in expect.items() if data.get(k) != v]
    check("JSON-LD identifikacijski podatki so pravilni", not bad, "; ".join(bad))
    geo = data.get("geo", {})
    near = abs(geo.get("latitude", 0) - 45.5730279) < 0.005 and abs(geo.get("longitude", 0) - 15.2922012) < 0.005
    check("JSON-LD geotocka je pri sedezu (Griblje 63A)", near, str(geo))
    addr = data.get("address", {})
    check("JSON-LD naslov je popoln",
          addr.get("streetAddress") == "Griblje 63A" and addr.get("postalCode") == "8332",
          json.dumps(addr, ensure_ascii=False))
    check("JSON-LD ne objavlja nepotrjenega delovnega casa",
          "openingHoursSpecification" not in json.dumps(data, ensure_ascii=False))
    logo = data.get("logo", "")
    check("JSON-LD logo kaze na pravo datoteko",
          logo.endswith("/img/logotip-bela.png") and os.path.isfile(os.path.join(ROOT, "img/logotip-bela.png")),
          logo)


# ---------------------------------------------------------------- 5.kontrasti
def luminance(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def check_contrasts():
    css = read("css/style.css")
    root = re.search(r":root\{(.*?)\}", css, re.S)
    if not check("CSS vsebuje blok :root", bool(root)):
        return
    palette = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", root.group(1)))
    # (oznaka, barva besedila, barva ozadja, najmanjse razmerje)
    pairs = [
        ("kicker na smetani", palette.get("amber-deep"), "#faf6ef", 4.5),
        ("kicker.light na temnem lesu", palette.get("amber-bright"), "#4a2c14", 4.5),
        ("gumb primarni + bela", "#ffffff", palette.get("brand"), 4.5),
        ("gumb primarni hover + bela", "#ffffff", palette.get("brand-dark"), 4.5),
        ("WhatsApp gumb + bela", "#ffffff", palette.get("wa"), 4.5),
        ("WhatsApp hover + bela", "#ffffff", palette.get("wa-dark"), 4.5),
        ("stepnum + bela", "#ffffff", palette.get("brand"), 4.5),
        ("aktivna navigacija + bela", "#ffffff", palette.get("brand"), 4.5),
        ("glavno besedilo na smetani", palette.get("ink"), "#faf6ef", 4.5),
        ("pomožno besedilo na smetani", palette.get("muted"), "#faf6ef", 4.5),
        ("noga", palette.get("foot-text", "#cbb896"), "#241509", 4.5),
        ("noga, drobni tisk", palette.get("foot-tiny", "#b39a78"), "#241509", 4.5),
        ("fokusni obroc na smetani", palette.get("brand"), "#faf6ef", 3.0),
        ("fokusni obroc na temnem", palette.get("amber-bright"), "#241509", 3.0),
        ("chip izbran", "#241509", palette.get("amber-bright"), 4.5),
        ("podpis slike na temnem", "#cdbca4", "#241509", 4.5),
    ]
    fails = []
    for label, fg, bg, need in pairs:
        if not fg or not bg:
            fails.append(f"{label}: manjka vnesena barva")
            continue
        v = ratio(fg, bg)
        if v < need:
            fails.append(f"{label} {v:.2f}:1 < {need}:1 ({fg} na {bg})")
    check("WCAG 2.2 AA kontrasti izracunani iz palete", not fails, "; ".join(fails))
    # mrtve barske spremenljivke
    unused = [k for k in palette if f"--{k}" not in css.replace(root.group(1), "", 1)]
    check("Vse barske spremenljivke so v uporabi", not unused, ", ".join("--" + u for u in unused))


# ---------------------------------------------------------------- 6.zabranjeno
BANNED = {
    "mnenja strank (sekcija)": 'id="mnenja"',
    "ocena z zvezdicami": "rev-card",
    "nepreverjeno stevilo del": "500+",
    "napacna davcna": "SI16668442",
    "napacen datum registracije": "2009",
    "izmisljen kraj v napisu": "Beltinci",
    "mrtva JS referenca": "formOk",
    "zdruzeni CSS sloj": "style2.css",
    "lazna trditev o garanciji": "5 let garancije",
    "meta keywords": "name=\"keywords\"",
    "prazen src": 'src=""',
    "nepojasnjena vizitka kot realizacija": "vizitka-ograje-lozar",
    "slika z vtisnjenim napisom": "delo-nadstresek",
    "nepreverjeno stevilo pogledov v napisu": "trije pogledi",
    "nepreverjeno stevilo fotografij v altu": "Tri fotografije",
    "nepreverjen password/secret": "ghp_",
}


def check_banned():
    corpus = ""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "img/arhiv")]
        for fn in filenames:
            if fn.endswith((".html", ".css", ".js", ".xml", ".txt", "_headers")) or fn == "_headers":
                corpus += read(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    hits = [f"{label} ({needle})" for label, needle in BANNED.items() if needle in corpus]
    check("Nobene zabranjene trditve ni v gradi", not hits, "; ".join(hits))


# ---------------------------------------------------------------- 7.filtri
def check_filters(html):
    chips = re.findall(r'<button class="chip" data-f="([^"]+)"', html)
    cats = set()
    for raw in re.findall(r'data-cat="([^"]+)"', html):
        cats.update(raw.split())
    unknown = sorted(cats - set(chips))
    empty = [c for c in chips if c != "all" and c not in cats]
    check("Vse kategorije galerije imajo chip", not unknown, ", ".join(unknown))
    check("Vsak chip vrne vsaj eno realizacijo", not empty, ", ".join(empty))
    n = len(re.findall(r'<figure class="reveal" data-cat=', html))
    check("Galerija ima vec kot 8 realizacij", n >= 8, f"najdenih {n}")


# ---------------------------------------------------------------- 7b.napisi
# Napis pod sliko mora povedati, kaj je na njej. Genericna beseda ("Detajl",
# "Vratca") je bila prav tisto, kar je stranka ocutila kot manjkajoc opis.
GENERICNE_NAPISE = {
    "detajl", "detajli", "uvip", "uvipi", "pogled", "pogledi", "delo", "slika",
    "realizacija", "realizacije", "vratca", "balkon", "ograja", "terasa",
    "fasada", "nadstresek", "nadstrešek", "brez napisa",
}
MOTIVI = ("ograj", "teras", "fasad", "nadstreš", "balkon", "podzid", "stopnic",
          "letv", "obloga", "podest", "nasip", "gramoz", "vhod", "dveri")


def check_captions(html):
    figs = re.findall(r'<figure class="reveal" data-cat=[^>]*>(.*?)</figure>', html, re.S)
    napisi = [re.search(r"<figcaption>(.*?)</figcaption>", f, re.S) for f in figs]
    manjkajoc = [i for i, n in enumerate(napisi, 1) if not n or not n.group(1).strip()]
    check("Vsaka realizacija ima napis", not manjkajoc, f"figure {manjkajoc}")

    besedila = [n.group(1).strip() for n in napisi if n]
    prani = [re.sub(r"[.!?:\u2014\-]+$", "", b).strip().lower() for b in besedila]
    genericni = [b for b, p in zip(besedila, prani) if p in GENERICNE_NAPISE]
    check("Napis ni genericna beseda", not genericni, "; ".join(genericni))

    kratki = [b for b in besedila if len(b) < 15]
    check("Napis je dovolj dolg, da kaj pove", not kratki, "; ".join(kratki))

    brez_motiva = [b for b in besedila if not any(k in b.lower() for k in MOTIVI)]
    check("Napis omenja dejanski motiv", not brez_motiva, "; ".join(brez_motiva))

    alti = re.findall(r'<img src="img/[^"]+" alt="([^"]+)"', html)
    prazni_alti = [i for i, a in enumerate(alti, 1) if len(a) < 20]
    check("Alt besedilo slike je opisno", not prazni_alti, f"indeksi {prazni_alti}")


# ---------------------------------------------------------------- 8.CSP
def check_csp(html):
    m = re.search(r"<script>(document\.documentElement[^<]*)</script>", html)
    if not check("V glavi je ena vrstica inline JS", bool(m)):
        return
    digest = "sha256-" + base64.b64encode(hashlib.sha256(m.group(1).encode("utf-8")).digest()).decode()
    headers = read("_headers")
    check("V _headers je geslo inline skripte", digest in headers, digest)

    meta = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', html)
    if not check("V HTML je meta CSP (edini, ki ga GitHub Pages dejansko izrsi)", bool(meta)):
        return
    mp = meta.group(1)
    check("Meta CSP ima isto geslo kot _headers", digest in mp, digest)

    def src_of(policy, directive):
        for part in policy.split(";"):
            if part.strip().startswith(directive):
                return part.strip()
        return ""

    check("Meta CSP ne dopusca 'unsafe-inline' za skripte",
          "unsafe-inline" not in src_of(mp, "script-src"), src_of(mp, "script-src"))
    check("Meta CSP ne dopusca 'unsafe-inline' za sloge",
          "unsafe-inline" not in src_of(mp, "style-src"), src_of(mp, "style-src"))
    check("Meta CSP se ne zanaa na direktive, ki jih meta prezre",
          "frame-ancestors" not in mp and "report-uri" not in mp)
    check("Noben element nima inline sloga", 'style="' not in html,
          "inline slog bi zahteval 'unsafe-inline' v style-src")

    hp = re.search(r"Content-Security-Policy:\s*(.+)", headers)
    pol = hp.group(1) if hp else ""
    need = ["default-src", "script-src", "connect-src", "frame-ancestors", "base-uri", "object-src"]
    miss = [d for d in need if d + " " not in pol]
    check("CSP v _headers doloca vse kljucne direktive", not miss, ", ".join(miss))
    check("CSP v _headers ne dopusca 'unsafe-inline'",
          "unsafe-inline" not in pol and "unsafe-eval" not in pol,
          src_of(pol, "script-src") or src_of(pol, "style-src"))
    check("Meta CSP doloca enake direktive kot _headers",
          all(d + " " in mp or d == "frame-ancestors" for d in need),
          ", ".join(d for d in need if d + " " not in mp))
    for h in ("Strict-Transport-Security", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"):
        check(f"V _headers je glava {h}", h in headers)
    check("Meta referrer je enak glavi v _headers",
          'name="referrer" content="strict-origin-when-cross-origin"' in html)


# ---------------------------------------------------------------- 9.rep
def check_tail():
    for f in ("robots.txt", "sitemap.xml", "404.html", "_headers", "zasebnost.html", ".gitignore", "README.md"):
        check(f"Datoteka {f} obstaja", os.path.isfile(os.path.join(ROOT, f)))
    sm = read("sitemap.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    bad = []
    for u in urls:
        if not u.startswith(SITE_ORIGIN):
            bad.append(f"{u}: izven domene")
            continue
        rel = u[len(SITE_ORIGIN):].strip("/")
        if rel and not os.path.isfile(os.path.join(ROOT, rel)):
            bad.append(u)
    check("Sitemap kaze samo na obstajajoca mocista", not bad, "; ".join(bad))
    check("Sitemap ne vsebuje 404.html", "404" not in sm)
    rb = read("robots.txt")
    check("robots.txt napotuje na sitemap", "sitemap.xml" in rb.lower())
    idx = read("index.html")
    check("canonical je domena brez koncnog podrocja",
          f'href="{SITE_ORIGIN}/"' in idx)
    check("og:image je absolutni URL",
          f'property="og:image" content="{SITE_ORIGIN}/img/' in idx)


# ---------------------------------------------------------------- 10.obrazec
def check_form(html, js):
    check("Obrazec nima lazne akcije", 'action="#"' not in html and "<form" in html)
    check("Obrazec ima podatke o posiljni poti", 'data-endpoint=' in html)
    check("JS ne sklicuje mrtvega #formOk", "formOk" not in js)
    for el in ("formResult", "formMsg", "formActions", "sendMail", "sendWa"):
        check(f"Element #{el} je v HTML in JS", el in html and el in js)
    check("Obrazec ima novalidate (validacijo vodi JS)", "novalidate" in html)
    forma = html.split('id="quoteForm"', 1)[-1].split("</form>", 1)[0]
    manjkajo = []
    for tag in re.findall(r"<input\b[^>]*>", forma):
        if 'type="checkbox"' in tag or 'name="podjetje"' in tag:
            continue
        if "autocomplete=" not in tag:
            manjkajo.append(re.search(r'name="([^"]+)"', tag).group(1))
    check("Vsako polje ima autocomplete", not manjkajo, "brez: " + ", ".join(manjkajo))
    check("GDPR dolocilo vsebuje rok hrambe", bool(re.search(r"hranim najve[čc] 12 mesecev", html)))
    note = forma.split('class="form-note"', 1)[-1]
    note = re.sub(r"<[^>]+>", " ", note)[:400]
    check("Besedilo ob obrazcu ne obljublja spletne posiljke",
          not any(w in note for w in ("takoj prejmete", "bo poslano", "poslana", "potrditveno", "samodejno posl"))
          and ("sestavi" in note or "pripravi" in note),
          note[:120])


# ---------------------------------------------------------------- 11.jezik
def prose_of(html):
    """Vidi besedilo: slogi in oznake ven, zapiralne oznake blokov presledek."""
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html, flags=re.S)
    t = re.sub(r"</(p|li|h1|h2|h3|figcaption|dd|dt|div|summary|blockquote)>", " ", t)
    t = re.sub(r"<[^>]+>", "", t)
    return t


def check_language():
    bad = []
    for fname in ("index.html", "zasebnost.html", "404.html", "README.md"):
        raw = read(fname)
        if fname.endswith(".html"):
            text = prose_of(re.sub(r"```.*?```", " ", raw, flags=re.S))
            # meta vsebina se ne izrise, je pa viden naslov ob delitvi
            meta = " ".join(re.findall(r'<meta[^>]+content="([^"]+)"', raw))
        else:
            text = re.sub(r"```.*?```", " ", raw, flags=re.S)
            meta = ""
        flat = re.sub(r"\s+", " ", text)
        for src, label in ((flat, ""), (re.sub(r"\s+", " ", meta), "meta: ")):
            for w in ("neobligatorna", "Poi" + chr(353) + "čajte", "kvaliteto", "Daljaven", "Vsota fotografije",
                      "Na" + chr(269) + "rtuj svojega"):
                if w in src:
                    bad.append(fname + ": " + label + "'" + w + "'")
            for m in re.finditer(r"\S\s([,.;:!?])", src):
                bad.append(fname + ": " + label + "presledek pred '" + m.group(1) + "' pri '..."
                           + src[max(0, m.start() - 30):m.start() + 2] + "...'")
        for m in re.finditer(r"(\w)  +(\w)", text):
            bad.append(fname + ": dvojni presledek pri '" + m.group(1) + m.group(2) + "'")
    check("Slovenscina brez znanih napak", not bad, "; ".join(bad[:4]))


def check_readme():
    raw = read("README.md")
    bad = []
    for m in re.finditer(r"scripts/([A-Za-z0-9._-]+)", raw):
        if not os.path.isfile(os.path.join(ROOT, "scripts", m.group(1))):
            bad.append("scripts/" + m.group(1) + " ne obstaja")
    for m in re.finditer(r"`([a-z0-9._/-]+\.(?:html|css|js|py|sh|xml|txt))`", raw):
        p = os.path.join(ROOT, m.group(1))
        if not m.group(1).startswith("http") and not os.path.isfile(p) and "<" not in m.group(1):
            bad.append(m.group(1) + " ne obstaja")
    check("README sklicuje samo obstajajoca orodja", not bad, "; ".join(sorted(set(bad))[:4]))
    lower = raw.lower()
    check("README ne predstavlja _headers kot delujocih na GitHub Pages",
          "github pages" in lower and ("ignorira" in lower or "ne podpira" in lower),
          "manja opomba, da javni GitHub Pages datoteke _headers ne uposteva")
    check("README opisuje obe razlicici CSP",
          "meta http-equiv" in lower and "_headers" in lower)


def check_fixed_bar():
    css = read("css/style.css")
    rob = "env(safe-area-inset-bottom)"
    vrstice = re.findall(r"\.sticky-call\{([^}]*)\}", css)
    check("Fiksna vrstica na dnu upošteva varnostni rob zaslona",
          any(rob in v for v in vrstice), "; ".join(vrstice[:2]))
    odmiki = re.findall(r"body\{padding-bottom:([^}]+)\}", css)
    check("Odmik telesa pod vrstico zraste z varnostnim robom",
          any(rob in v for v in odmiki), "; ".join(odmiki))
    dna = re.findall(r"\.to-top\{bottom:([^;}]+)", css)
    check("Gumb na vrh ostane nad vrstico tudi z varnostnim robom",
          any(rob in v for v in dna), "; ".join(dna))


def check_ci():
    rel = os.path.join(".github", "workflows", "preveri.yml")
    obstaja = os.path.isfile(os.path.join(ROOT, rel))
    check("Workflow za vrata obstaja", obstaja, rel)
    if not obstaja:
        return
    yml = read(rel)
    # Upostevaj samo dejanske run ukaze: komentar, ki omenja skripto,
    # ne sme zashteti, da se vrata v CI res poganjajo.
    ukazi = " ".join(re.findall(r"^\s*run:\s*(.+)$", yml, re.M))
    check("Workflow zazene vrata", "scripts/preveri.py" in ukazi)
    check("Workflow zazene mutacijski test", "mutacijski-test.py" in ukazi)
    check("Workflow namesti odvisnosti vrat", "requirements.txt" in ukazi)
    check("Workflow ne uporablja skritih gesel", "secrets." not in yml)


def main():
    verbose = "--verbose" in sys.argv
    html = read("index.html")
    js = read("js/main.js")
    prehodi = [
        ("oznake", check_markup),
        ("slike", lambda: check_pictures(html)),
        ("dimenzije", lambda: check_dimensions(html)),
        ("teza", check_weight),
        ("povezave", lambda: check_links(html)),
        ("json-ld", lambda: check_jsonld(html)),
        ("barve", check_contrasts),
        ("trditve", check_banned),
        ("filtri", lambda: check_filters(html)),
        ("napisi", lambda: check_captions(html)),
        ("csp", lambda: check_csp(html)),
        ("rep", check_tail),
        ("obrazec", lambda: check_form(html, js)),
        ("jezik", check_language),
        ("readme", check_readme),
        ("vrstica", check_fixed_bar),
        ("ci", check_ci),
    ]
    for name, fn in prehodi:
        try:
            fn()
        except Exception as exc:
            check("Prehod {} je tekel do konca".format(name), False,
                  "{}: {}".format(type(exc).__name__, exc))

    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        if ok and not verbose:
            continue
        print(("  OK  " if ok else "  NOK ") + name + (("  ->  " + detail) if detail and (not ok or verbose) else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} kontrol uspelo")
    if failed:
        print("NOK")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
