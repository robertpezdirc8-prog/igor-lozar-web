# Spletna stran — Ograje Lozar (Igor Lozar s.p.)

Enostranska statična spletna stran za podjetnika **Igor Lozar s.p.**, ki posluje kot **Ograje Lozar** (Griblje 63A, 8332 Gradac): izdelava in montaža lesenih, WPC, panelnih in kovinskih ograj, lesenih nadstreškov, WPC teras in fasad.

Brez gradbenega koraka in brez odvisnosti. HTML + CSS + vanilla JS, gostovanje je GitHub Pages.

## Živa stran

<https://robertpezdirc8-prog.github.io/igor-lozar-web/>

## Preverjeni podatki podjetja

| Podatek | Vrednost | Vir |
|---|---|---|
| Naziv | Ograje Lozar, Igor Lozar s.p. | ogranadstreski.eu / register |
| Sedež | Griblje 63A, 8332 Gradac | register |
| Matična številka | 5546572000 | bizi.si, companywall.si |
| Davčna številka | 22822577 | register |
| ID za DDV | SI22822577 | register |
| Registracija | 4. 6. 1996 | register |
| Osnovna dejavnost | F43.320 Vgrajevanje stavbnega pohištva | register |
| Telefon | 041 276-195 | ogranadstreski.eu |
| E-pošta | lesne.storitve@gmail.com | ogranadstreski.eu |
| Ge. točka sedeža | 45.5730279, 15.2922012 | Nominatim (posodobljeno 2026-10-21) |

> Prejšnja različica strani je navajala davčno SI16668442 in registracijo 15. 1. 2009. Oba podatka sta bila napačna; popravljena sta 21. 10. 2026.

## Struktura

```
index.html        ena stran: storitve, zakaj mi, postopek, realizacije, o nas, FAQ, kontakt
zasebnost.html    GDPR izjava (upravljavec, piškoti, pisave, obrazec, hramba, pravice)
404.html          napaka 404 z absolutnimi potmi
robots.txt        dovoljenje + naslov sitemap
sitemap.xml       dve URL-ja
_headers          CSP, HSTS, nosniff, cache — javni GitHub Pages jih ignorira (gl. "Glave in gostitelj")
css/style.css     enoten sloj (bivša style2.css je združena in izbrisana)
js/main.js        meni, scroll-spy, reveal, števeci, filtri, lightbox, obrazec
img/              JPG (izvirnik) + WebP + AVIF za vsako fotografijo
img/arhiv/        umaknjeni viri (vizitka, kolaži, clipart) — niso več povezani
scripts/          orodja za vzdrževanje
requirements.txt  Pillow, ki ga potrebuje vrata
.github/workflows/preveri.yml  vrata na GitHub Actions (gl. "Vrata v CI")
```

## Slike

Vsaka fotografija je shranjena kot `img/<ime>.jpg`, iz nje pa sta generirana še `.webp` in `.avif`. V HTML je vsaka slika ovita v `<picture>` z vrstnim redom AVIF → WebP → JPEG, z izraženima `width`/`height` (brez CLS) in `loading="lazy"` (razen hero, ki ima `fetchpriority="high"`).

Dodajanje nove fotografije:

```bash
cp nova-fotografija.jpg img/ograja-nova.jpg
sh scripts/slike.sh          # regenerira WebP + AVIF za vse datoteke v img/
```

Zahteva ImageMagick 7 (`magick`). Pod `convert` se na Windows nahaja sistemsko orodje za diskove, zato skript uporablja izključno `magick`.

**Pogoj za novo sliko:** na njej ne sme biti vtisnjenih napisov, vodnih žigov ali dela vizitke. Takšne datoteke grejo v `img/arhiv/`, ne na stran.

## Obrazec za povpraševanje

GitHub Pages ne more poslati e-pošte, zato obrazec **brez strežnika ne pošilja ničesar**. Uporabnik izpolni polja, stran sestavi sporočilo in ponudi dve poti: `mailto:` v njegovem e-poštnem programu ali `wa.me` v WhatsAppu.

Ko bo na voljo pošiljna storitev (npr. Formspree), se vklopi z enim atributom:

```html
<form id="quoteForm" data-endpoint="https://formspree.io/f/XXXX">
```

Obenem je treba domeno dodati v `connect-src` **na obeh mestih** CSP (`_headers` in meta oznaka v `index.html`), sicer jo preostali politiki zablokirata. Dokler je `data-endpoint` prazen, besedilo ob obrazcu (`.form-note`) opisuje dejansko stanje — če se pošiljka vklopi, se mora spremeniti tudi ono in 4. točka `zasebnost.html`.

## Lokalni zagon in preverjanje

```bash
python -m http.server 8090         # http://127.0.0.1:8090
python scripts/preveri.py          # vrsta kontrol: HTML, povezave, kontrast, CSP, slike
```

Pod `python3` je na Windows namesto pravega Pythona namestena preusmeritev iz Microsoftove trgovine, ki ne deluje; skript uporablja `python` (3.11 ali novejši, z `Pillow`).

`scripts/preveri.py` je edini vir resnice o tem, ali je stran pripravljena za oddajo. Izpiše seznam kontrol in konča z `OK` ali `NOK`. Vsaka kontrola je bila preizkušena tudi na vsiljeni napaki (mutacijski test), da ne laže.

## Vrata v CI

`.github/workflows/preveri.yml` zažene `python scripts/preveri.py --verbose` in nato `python scripts/mutacijski-test.py` — ob vsakem pushu na `main`, ob vsakem pull zahtevku in ob ročnem zagonu. Oba tečeta na Ubuntu izvajalcu s Pythonom 3.11 in knjižnico `Pillow`, ki ju določa `requirements.txt`, zato rezultat ni odvisen od tega, ali je kdo pozabil ugniti vrata na svojemu računalniku.

Workflow je statusna preverba in ne zapora za objavo: javni GitHub Pages postreže branch `main` sam, tudi če vrata javijo NOK. Pred pushom jih je zato treba ugniti lokalno.

## Glave in gostitelj

Datoteko `_headers` razumeta Cloudflare Pages in Netlify. **Javni GitHub Pages je ignorira** in postreže svoj fiksni nabor glav; izmerjeno 21. 10. 2026 na `https://robertpezdirc8-prog.github.io/igor-lozar-web/`:

| Glava | `_headers` obljublja | GitHub Pages dejansko postreže |
|---|---|---|
| Content-Security-Policy | da | ne (je je) |
| Cache-Control za `/img/*` | `max-age=31536000, immutable` | `max-age=600` (merjeno na `img/hero.jpg`) |
| X-Content-Type-Options, Referrer-Policy, Permissions-Policy, X-Frame-Options | da | ne |
| Strict-Transport-Security | `max-age=31536000; includeSubDomains` | `max-age=31556952` (svoj, brez includeSubDomains) |

Zato je varnostna politika zapisana **dvakrat**:

1. v `<head>` kot `<meta http-equiv="Content-Security-Policy">` — edini del, ki na GitHub Pages dejansko deluje;
2. v `_headers` — velja takoj, ko stran preide na Cloudflare Pages ali Netlify.

Meta različica namenoma **brez** `frame-ancestors`: brskalnik te direktive v meta oznaki prezre, zato je izpisana samo v `_headers`. Posledica na današnjem gostitelju: zaščita pred vtikanjem v okvir pride šele s prestavitvijo. Pravi razlog št. 1 za prestavitev je dolgo predpomnjenje fotografij, ki ga GitHub Pages ne da.

Če se gostitelj ali domena spremenita, je treba posodobiti `canonical`, `og:url`, `sitemap.xml`, `robots.txt` in absolutne poti v `404.html` ter `zasebnost.html`. `scripts/preveri.py` drži obe različici CSP usklajeni (isti `sha256` izpis).

## Dostopnost

- WCAG 2.2 AA kontrasti izračunani na razredke barvne palete (normalno besedilo ≥ 4,5:1, veliko in grafični elementi ≥ 3:1).
- Vse slike imajo `alt`, ki opisuje dejanski motiv — ne imena datoteke in ne napačnega motiva.
- Fokusni obroč je dvotonen (`#b45309` na svetlem, `#eab308` na temnem), da ostane viden na obeh podlagah.
- Lightbox: fokusna past, `Esc`, puščici, gumb se vrne na odprto povezavo.
- `prefers-reduced-motion` izklopi animacije; vsebina je brez JS videna v celoti (razred `.js` na `<html>`).

## Česa stran ne trdi

Stran namenoma **nima** mnenj strank, ocen, zvezdic, števila izvedenih projektov niti zagotovljenih garancijskih dob. Razlog: teh trditev ni mogoče podpreti z virom, lažne ocene pa so v EU prepovedane (Direktiva 2005/29/EC, 7. člen). Ko Igor zbere resnična priporočila z imenom in datumom, se lahko vrnejo.

## Še ni potrjeno (potreben dogovor z lastnikom)

1. **Delovni čas** (pon–pet 8–18, sob 8–13) je prevzet iz starejše verzije strani in ni nikjer potrjen. Ker bi ga JSON-LD pretvoril v Googleov značko "odprto zdaj", je namenoma **izpuščen iz strukturiranih podatkov**, dokler ga ne potrdi Igor.
2. **Obseg garancije** za WPC in lesene izvedbe.
3. **Pravna istovetnost** profila na ogranadstreski.eu (ali gre za isto podjetje ali posrednika).

## Oddaja

```bash
git push origin main        # GitHub Pages samodejno objavi main
```

Stran je na branchu `main`, `build_type: legacy`, HTTPS vsiljen. Custom domena še ni priklopljena; če bo, je treba posodobiti `canonical`, `og:url`, `sitemap.xml`, `robots.txt` in absolutne poti v `404.html` / `zasebnost.html`.
