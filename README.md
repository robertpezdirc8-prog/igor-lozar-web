# Spletna stran — Ograje Lozar (Igor Lozar s.p.)

Profesionalna enostranska spletna stran za podjetnika **Igor Lozar s.p.** (Ograje Lozar), Griblje 63A, 8332 Gradac — izdelava in montaža lesenih, WPC, panelnih in kovinskih ograj, lesenih nadstreškov s steklom ter WPC teras in fasad.

## Viri podatkov (preverjeno na spletu)
- ograje-nadstreski.eu — uradni profil OGRAJE LOZAR (storitve, telefonska številka 041/276-195, e-pošta lesne.storitve@gmail.com, fotografije del)
- bizi.si / companywall.si — matična 5546572000, naslov Griblje 63A, dejavnost Lesna dejavnost; registracija 15. 1. 2009
- mojmojster.net, moja-dejavnost.si, Facebook stran "Ograje Lozar"

## Struktura
- `index.html` — storitve, zakaj mi, postopek v 5 korakih, galerija realizacij (lightbox), o nas z matičnimi podatki, mnenja, FAQ, kontakt z obrazcem povpraševanja; JSON-LD (LocalBusiness/HomeAndConstructionBusiness)
- `css/style.css` — leseno-medena paleta, tipografija Fraunces + Inter, mobilno-najprej odzivnost (breakpointi 1024/860/560/380 px), reduced-motion
- `js/main.js` — hamburger meni, scroll-spy, reveal animacije, števeci, lightbox, potrditev obrazca
- `img/` — prave fotografije dela podjetja (iz_uradnega profila) + logotip

## Zagon
```bash
python3 -m http.server 8090
# ali odpri index.html neposredno
```

## GitHub Pages
Repo: `igor-lozar-web` → Pages URL: `https://robertpezdirc8-prog.github.io/igor-lozar-web/`
