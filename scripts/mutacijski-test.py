#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mutacijski test za preveri.py.

Vsilo pokvari eno samo stvar v kopiji repa, zazene preverjalni pas in
preveri, ali je točno tista kontrola javila NOK. Kontrola, ki je nikoli ne
vidim falšati, ne pomeni nicesar — morda vedno vrne OK.

Uporaba:  python scripts/mutacijski-test.py
"""

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (nacin, datoteka, staro, novo, kontrola, ki mora javiti NOK)
MUTACIJE = [
    ("patch", "index.html", "<h3>Montaža in predaja</h3>", "<h3>Montaža in predaja",
     "Uravnotezenost oznak v index.html"),
    ("patch", "index.html", 'loading="lazy" decoding="async"', 'decoding="async"',
     "Vse <img> imajo alt/width/height/loading/decoding"),
    ("patch", "index.html", '<source type="image/avif" srcset="img/detajl-ograj-1.avif">', "",
     "Vse <img> so v <picture> z AVIF in WebP"),
    ("patch", "index.html", 'src="img/detajl-ograj-1.jpg"', 'src="img/ne-obstaja.jpg"',
     "Vse referencirane datoteke obstajajo"),
    ("patch", "index.html",
     'alt="Antracitna WPC ograja s horizontalnimi letvami na betonskem podzidu"', 'alt=""',
     "Noben alt ni prazen ali ime datoteke"),
    ("patch", "index.html", 'width="690" height="517" loading="lazy"',
     'width="700" height="517" loading="lazy"',
     "Dimenzije v HTML ustrezajo slikam (brez CLS)"),
    ("grow", "img/hero-realizacije.avif", 400000, None, "LCP slika znotraj prorasuna"),
    ("patch", "index.html", 'href="#galerija"', 'href="#galeriya"',
     "Vse znotrajstranske sidrne povezave imajo cilj"),
    ("patch", "index.html", "https://robertpezdirc8-prog.github.io",
     "http://robertpezdirc8-prog.github.io", "Nobena povezava ni navadni HTTP"),
    ("patch", "index.html", '"vatID": "SI22822577"', '"vatID": "SI16668442"',
     "JSON-LD identifikacijski podatki so pravilni"),
    ("patch", "index.html", '"latitude": 45.5730279', '"latitude": 46.9123456',
     "JSON-LD geotocka je pri sedezu (Griblje 63A)"),
    ("patch", "index.html", '"@type": "GeoCoordinates"',
     '"openingHoursSpecification": [], "@type": "GeoCoordinates"',
     "JSON-LD ne objavlja nepotrjenega delovnega casa"),
    ("patch", "index.html", "img/logotip-bela.png", "img/pot-laza.png",
     "JSON-LD logo kaze na pravo datoteko"),
    ("patch", "css/style.css", "--amber-deep:#9c6027", "--amber-deep:#c98a3d",
     "WCAG 2.2 AA kontrasti izracunani iz palete"),
    ("patch", "css/style.css", "--amber:#c98a3d;", "--amber:#c98a3d; --neuporabljena:#123456;",
     "Vse barske spremenljivke so v uporabi"),
    ("patch", "index.html", "Zanesljivo in natančno",
     "Zanesljivo in natančno — 500+ oddanih ograj", "Nobene zabranjene trditve ni v gradi"),
    ("patch", "index.html", 'data-cat="nadstresek terasa wpc"',
     'data-cat="nadstresek terasa wpc strip"', "Vse kategorije galerije imajo chip"),
    ("patch", "index.html", '<button class="chip" data-f="fasada"',
     '<button class="chip" data-f="brezdel"', "Vsak chip vrne vsaj eno realizacijo"),
    ("patch", "index.html", "classList.add('js')", "classList.add('js2')",
     "V _headers je geslo inline skripte"),
    ("patch", "index.html", '<meta http-equiv="Content-Security-Policy" content="default-src',
     '<meta name="x-csp-je-izzivel" content="default-src',
     "V HTML je meta CSP (edini, ki ga GitHub Pages dejansko izrsi)"),
    ("patch", "index.html", "sha256-/x7W7R75k8Roq0WaVRQX9blP4OufE5xbAdzklGxsgpw=",
     "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
     "Meta CSP ima isto geslo kot _headers"),
    ("patch", "index.html", 'class="hp"', 'style="position:absolute;left:-9999px"',
     "Noben element nima inline sloga"),
    ("patch", "index.html", "object-src 'none'\">", "frame-ancestors 'none'; object-src 'none'\">",
     "Meta CSP se ne zanaa na direktive, ki jih meta prezre"),
    ("patch", "index.html", "script-src 'self' 'sha256-",
     "script-src 'self' 'unsafe-inline' 'sha256-",
     "Meta CSP ne dopusca 'unsafe-inline' za skripte"),
    ("patch", "_headers", "script-src 'self' 'sha256-",
     "script-src 'self' 'unsafe-inline' 'sha256-",
     "CSP v _headers ne dopusca 'unsafe-inline'"),
    ("patch", "_headers", "connect-src 'self';", ";",
     "CSP v _headers doloca vse kljucne direktive"),
    ("patch", "_headers", "Strict-Transport-Security:", "Strict-Transport-Sec:",
     "V _headers je glava Strict-Transport-Security"),
    ("patchall", "README.md", "ignorira", "uporablja",
     "README ne predstavlja _headers kot delujocih na GitHub Pages"),
    ("delete", ".github/workflows/preveri.yml", None, None,
     "Workflow za vrata obstaja"),
    ("patch", ".github/workflows/preveri.yml",
     "run: python scripts/preveri.py --verbose", "run: echo vrata preskocena",
     "Workflow zazene vrata"),
    ("patch", ".github/workflows/preveri.yml",
     "run: python scripts/mutacijski-test.py", "run: echo hitro",
     "Workflow zazene mutacijski test"),
    ("patch", ".github/workflows/preveri.yml",
     "run: python -m pip install -r requirements.txt", "run: echo ni namestitve",
     "Workflow namesti odvisnosti vrat"),
    ("patch", ".github/workflows/preveri.yml",
     "name: Preveri stran",
     "name: Preveri stran\nenv:\n  TOK: ${{ secrets.GITHUB_TOKEN }}",
     "Workflow ne uporablja skritih gesel"),
    ("delete", "robots.txt", None, None, "Datoteka robots.txt obstaja"),
    ("patch", "sitemap.xml",
     "<loc>https://robertpezdirc8-prog.github.io/igor-lozar-web/zasebnost.html</loc>",
     "<loc>https://robertpezdirc8-prog.github.io/igor-lozar-web/zasebnost.html</loc>\n  "
     "<loc>https://robertpezdirc8-prog.github.io/igor-lozar-web/ne-najdem.html</loc>",
     "Sitemap kaze samo na obstajajoca mocista"),
    ("patch", "sitemap.xml", "/igor-lozar-web/zasebnost.html", "/igor-lozar-web/404.html",
     "Sitemap ne vsebuje 404.html"),
    ("patch", "robots.txt", "/sitemap.xml", "/karta-smeri.xml",
     "robots.txt napotuje na sitemap"),
    ("patch", "index.html",
     '<link rel="canonical" href="https://robertpezdirc8-prog.github.io/igor-lozar-web/">',
     '<link rel="canonical" href="https://primer.si/">',
     "canonical je domena brez koncnog podrocja"),
    ("patch", "index.html",
     'content="https://robertpezdirc8-prog.github.io/igor-lozar-web/img/hero-realizacije.jpg"',
     'content="img/hero-realizacije.jpg"', "og:image je absolutni URL"),
    ("patch", "index.html", 'data-endpoint=""', "",
     "Obrazec ima podatke o posiljni poti"),
    ("patch", "index.html", "novalidate", "",
     "Obrazec ima novalidate (validacijo vodi JS)"),
    ("patch", "index.html", 'autocomplete="email"', "",
     "Vsako polje ima autocomplete"),
    ("patch", "index.html", "največ 12 mesecev", "dokler želiš",
     "GDPR dolocilo vsebuje rok hrambe"),
    ("patch", "index.html", "Spletna pošiljka je trenutno izklopljena",
     "Pošljite in takoj prejmete odgovor.",
     "Besedilo ob obrazcu ne obljublja spletne posiljke"),
    ("patch", "index.html", "<em>kakovost</em>", "<em>kvaliteto</em>",
     "Slovenscina brez znanih napak"),
    ("patch", "index.html", 'content="Ograje Lozar — kakovostne ograje',
     'content="Ograje Lozar — kvaliteto ograje', "Slovenscina brez znanih napak"),
    ("patch", "README.md", "scripts/preveri.py", "scripts/ne-obstaja.py",
     "README sklicuje samo obstajajoca orodja"),
    ("patch", "js/main.js", "formResult", "formOk",
     "JS ne sklicuje mrtvega #formOk"),
    ("patch", "index.html", 'id="formMsg"', 'id="formSporocilo"',
     "Element #formMsg je v HTML in JS"),
]


def run_gate(working):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, os.path.join(working, "scripts", "preveri.py")],
                          capture_output=True, text=True, cwd=working,
                          encoding="utf-8", errors="replace", env=env)
    out = proc.stdout or ""
    nok = set()
    for line in out.splitlines():
        if line.strip().startswith("NOK"):
            nok.add(line.split("NOK", 1)[1].strip().split("  ->")[0].strip())
    crash = ""
    if proc.returncode != 0 and not nok:
        err = (proc.stderr or "").strip()
        crash = err.splitlines()[-1][:160] if err else "koda {}, brez izpisa".format(proc.returncode)
    return proc.returncode, nok, out, crash


def fresh(working):
    if os.path.isdir(working):
        shutil.rmtree(working)
    shutil.copytree(ROOT, working, ignore=shutil.ignore_patterns(".git"))


def apply_mutation(working, spec):
    mode, rel, old, new, _ = spec
    path = os.path.join(working, rel)
    if mode == "grow":
        with open(path, "ab") as fh:
            fh.write(b"\0" * old)
    elif mode == "delete":
        os.remove(path)
    else:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if old not in text:
            raise AssertionError("zajemka ni v {}: {!r}".format(rel, old[:70]))
        out = text.replace(old, new) if mode == "patchall" else text.replace(old, new, 1)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(out)


def main():
    tmp = tempfile.mkdtemp(prefix="ograje-mut-")
    working = os.path.join(tmp, "w")
    try:
        fresh(working)
        code, nok, out, crash = run_gate(working)
        if code != 0:
            print("Izvorna kopija ni cista, mutacij ne izvajam:")
            for name in sorted(nok):
                print("  -", name)
            if crash:
                print("  ZBURJENOST:", crash)
            return 1
        print("Izvorna kopija: OK\n")

        escaped = []
        for spec in MUTACIJE:
            target = spec[4]
            fresh(working)
            try:
                apply_mutation(working, spec)
            except AssertionError as exc:
                print("  ZAJEMKA NI  {}".format(target))
                print("               {}".format(exc))
                escaped.append(target + " (zajemka ni)")
                continue
            _, nok, _, crash = run_gate(working)
            if target in nok:
                print("  ujeto       {}".format(target))
            elif crash:
                print("  ZBURJI      {}  -> pas je umrl: {}".format(target, crash))
                escaped.append(target + " (pas zbil, ne javi)")
            else:
                print("  ESPUCENO    {}  -> NOK javilo: {}".format(target, ", ".join(sorted(nok)) or "nic"))
                escaped.append(target)
        ujeta = len(MUTACIJE) - len(escaped)
        print("\n{} / {} kontrol ujelo vsiljeno napako".format(ujeta, len(MUTACIJE)))
        if escaped:
            print("Nepreverjene kontrolke:")
            for name in escaped:
                print("  -", name)
        return 1 if escaped else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
