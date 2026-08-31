#!/usr/bin/env python
"""Chaîne de build du site, pilotée depuis Python.

    .venv/bin/python build.py

1. Assemble la feuille source : tokens (design_tokens.py) + règles maison
   (assets/custom.css) + directive Tailwind.
2. Compile avec le binaire Tailwind autonome (aucun Node requis, fourni par
   le paquet pytailwindcss) vers static/css/app.css, minifié.
3. Génère les variantes WebP des photos et affiche le gain.

À relancer après toute modification des tokens, des templates ou des photos.
"""

import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

import design_tokens

RACINE = pathlib.Path(__file__).parent
SOURCE = RACINE / "assets" / "_source.css"
SORTIE = RACINE / "static" / "css" / "app.css"
IMAGES = RACINE / "static" / "img"
POLICE_TTF = RACINE / "assets" / "plus-jakarta-sans.ttf"


def compile_css() -> None:
    entete = (
        "/* Fichier généré par build.py — ne pas éditer à la main.\n"
        "   Tokens : design_tokens.py · Règles maison : assets/custom.css */\n"
        '@import "tailwindcss";\n'
        '@source "../templates";\n\n'
    )
    custom = (RACINE / "assets" / "custom.css").read_text(encoding="utf-8")
    SOURCE.write_text(f"{entete}{design_tokens.theme_css()}\n\n{custom}", encoding="utf-8")

    binaire = pathlib.Path(sys.executable).parent / "tailwindcss"
    resultat = subprocess.run(
        [str(binaire), "-i", str(SOURCE), "-o", str(SORTIE), "--minify"],
        capture_output=True, text=True,
    )
    if resultat.returncode != 0:
        sys.exit(f"Échec de la compilation CSS :\n{resultat.stderr}")
    print(f"CSS      static/css/app.css — {SORTIE.stat().st_size / 1024:.1f} Ko minifié")


def generer_favicon() -> None:
    """Produit l'icône d'onglet et l'icône d'écran d'accueil iOS.

    La marque est reconstruite depuis les tokens : changer la couleur primaire
    dans design_tokens.py suffit à régénérer une icône cohérente.
    """
    primaire = design_tokens.COLORS["primary"]
    secondaire = design_tokens.COLORS["secondary"]
    hexagone = ("M12 2.5 20 7v10l-8 4.5L4 17V7z")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <defs><linearGradient id="d" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{primaire}"/><stop offset="1" stop-color="{secondaire}"/>
  </linearGradient></defs>
  <rect width="24" height="24" rx="6" fill="url(#d)"/>
  <path d="{hexagone}" fill="none" stroke="white" stroke-width="1.8"
        stroke-linejoin="round"/>
</svg>
"""
    (RACINE / "static" / "favicon.svg").write_text(svg, encoding="utf-8")

    # Version bitmap pour iOS et les navigateurs sans favicon vectoriel.
    cote = 180
    icone = Image.new("RGB", (cote, cote), primaire)
    dessin = ImageDraw.Draw(icone)
    for y in range(cote):                       # dégradé vertical simple
        t = y / cote
        dessin.line([(0, y), (cote, y)], fill=(
            int(int(primaire[1:3], 16) + (int(secondaire[1:3], 16) - int(primaire[1:3], 16)) * t),
            int(int(primaire[3:5], 16) + (int(secondaire[3:5], 16) - int(primaire[3:5], 16)) * t),
            int(int(primaire[5:7], 16) + (int(secondaire[5:7], 16) - int(primaire[5:7], 16)) * t)))
    marque = ImageFont.truetype(str(POLICE_TTF), 104)
    marque.set_variation_by_axes([800])
    boite = dessin.textbbox((0, 0), "H", font=marque)
    dessin.text(((cote - boite[2]) / 2, (cote - boite[3]) / 2 - 8), "H",
                font=marque, fill="white")
    icone.save(RACINE / "static" / "apple-touch-icon.png", "PNG", optimize=True)
    print("Icônes   static/favicon.svg + apple-touch-icon.png")


def convertir_webp() -> None:
    """Double chaque JPEG en WebP ; les templates servent les deux via <picture>."""
    avant = apres = 0
    for jpeg in sorted(IMAGES.glob("*.jpg")):
        webp = jpeg.with_suffix(".webp")
        Image.open(jpeg).convert("RGB").save(webp, "WEBP", quality=80, method=6)
        avant += jpeg.stat().st_size
        apres += webp.stat().st_size
    print(f"Images   {len(list(IMAGES.glob('*.webp')))} WebP générés — "
          f"{avant / 1024:.0f} Ko de JPEG → {apres / 1024:.0f} Ko "
          f"({100 - apres * 100 // avant} % de moins)")


def generer_carte_sociale() -> None:
    """Compose l'image affichée quand un lien du site est partagé.

    1200 x 630 : le format lu par WhatsApp, Facebook, LinkedIn et X.
    """
    largeur, hauteur = 1200, 630
    fond = Image.open(IMAGES / "hero-equipe.jpg").convert("RGB")
    fond = fond.resize((largeur, int(largeur * fond.height / fond.width)), Image.LANCZOS)
    haut = max(0, (fond.height - hauteur) // 2)
    carte = fond.crop((0, haut, largeur, haut + hauteur))

    # Voile dégradé indigo → violet, pour que le texte reste lisible.
    voile = Image.new("RGB", (largeur, hauteur))
    dessin_voile = ImageDraw.Draw(voile)
    for x in range(largeur):
        t = x / largeur
        couleur = (int(79 + (124 - 79) * t),
                   int(70 + (58 - 70) * t),
                   int(229 + (237 - 229) * t))
        dessin_voile.line([(x, 0), (x, hauteur)], fill=couleur)
    carte = Image.blend(carte, voile, 0.82)

    dessin = ImageDraw.Draw(carte)
    titre = ImageFont.truetype(str(POLICE_TTF), 78)
    sous_titre = ImageFont.truetype(str(POLICE_TTF), 34)
    detail = ImageFont.truetype(str(POLICE_TTF), 26)

    # La police est variable : on force les graisses au lieu de tout rendre en 400.
    titre.set_variation_by_axes([800])
    sous_titre.set_variation_by_axes([500])
    detail.set_variation_by_axes([500])

    dessin.rounded_rectangle((80, 168, 140, 174), radius=3, fill="white")  # filet d'accent
    dessin.text((80, 196), "Hushlab", font=titre, fill="white")
    dessin.text((80, 306), "Vos projets avancent, on s'occupe du reste.",
                font=sous_titre, fill=(237, 233, 254))
    dessin.text((80, 372),
                "Sites web · QR & NFC · Réseaux sociaux · IA · Création d'entreprise",
                font=detail, fill=(199, 210, 254))
    dessin.text((80, 486), "Rabat, Maroc  ·  06 56 18 54 14", font=detail, fill=(199, 210, 254))

    carte.save(IMAGES / "og.jpg", "JPEG", quality=86, optimize=True)
    print(f"Partage  static/img/og.jpg — 1200x630, "
          f"{(IMAGES / 'og.jpg').stat().st_size / 1024:.0f} Ko")


if __name__ == "__main__":
    compile_css()
    generer_favicon()
    generer_carte_sociale()
    convertir_webp()
