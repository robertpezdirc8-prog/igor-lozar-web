#!/bin/sh
# Stisne vse postrežene fotografije v JPEG + WebP + AVIF.
# Znova zaženi po tem, ko Igor doda nove slike:  sh scripts/slike.sh
# img/arhiv/ se namenoma preskoči — tam izvirniki niso za objavo.
set -e
cd "$(dirname "$0")/.."

for src in img/*.jpg; do
  base="${src%.jpg}"
  magick "$src" -strip -interlace Plane -quality 82 "$src"
  magick "$src" -strip -quality 72 "$base.webp"
  magick "$src" -strip -quality 38 -define avif:crs=srgb "$base.avif"
done

for src in img/*.png; do
  base="${src%.png}"
  magick "$src" -strip -quality 72 "$base.webp"
  magick "$src" -strip -quality 65 "$base.avif"
done

echo "Zdaj posodobi width/height atribute v index.html, če se je kakšna slike spremenila."
magick identify -format "%f  %wx%h  %b\n" img/*.jpg img/*.webp img/*.avif img/*.png
