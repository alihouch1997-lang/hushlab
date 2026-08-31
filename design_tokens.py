"""Source de vérité unique du design system « Corporate Trust » de Hushlab.

Aucune couleur, ombre ou rayon n'est écrit en dur dans un template : tout part
d'ici. `theme_css()` traduit ces tokens en bloc `@theme` Tailwind v4, que
`build.py` compile en une feuille de style statique.
"""

# --- Couleurs ----------------------------------------------------------------
COLORS = {
    "background": "#F8FAFC",  # Slate 50   — fond de page
    "surface": "#FFFFFF",     # White      — cartes et éléments surélevés
    "primary": "#4F46E5",     # Indigo 600 — couleur de marque
    "secondary": "#7C3AED",   # Violet 600 — dégradés et accents
    "ink": "#0F172A",         # Slate 900  — texte principal
    "muted": "#64748B",       # Slate 500  — texte secondaire
    "success": "#10B981",     # Emerald 500
    "line": "#E2E8F0",        # Slate 200  — bordures
}

# --- Ombres colorées (la signature visuelle du style) ------------------------
SHADOWS = {
    "soft": "0 4px 20px -2px rgba(79, 70, 229, 0.10)",
    "lifted": ("0 10px 25px -5px rgba(79, 70, 229, 0.15), "
               "0 8px 10px -6px rgba(79, 70, 229, 0.10)"),
    "button": "0 4px 14px 0 rgba(79, 70, 229, 0.30)",
    "glow": "0 0 20px rgba(79, 70, 229, 0.50)",
}

FONT_STACK = '"Plus Jakarta Sans", ui-sans-serif, system-ui, sans-serif'

# Dégradé primaire, réutilisé partout (boutons, textes, badges).
GRADIENT = "bg-gradient-to-r from-indigo-600 to-violet-600"


def theme_css() -> str:
    """Rend le bloc `@theme` consommé par Tailwind v4.

    Les rayons (`rounded-lg` = 8 px, `rounded-xl` = 12 px) correspondent déjà
    aux valeurs par défaut de Tailwind v4 : inutile de les redéfinir.
    """
    lignes = [
        f"  --color-background: {COLORS['background']};",
        f"  --color-surface: {COLORS['surface']};",
        f"  --color-ink: {COLORS['ink']};",
        f"  --color-muted: {COLORS['muted']};",
        f"  --color-line: {COLORS['line']};",
        f"  --color-brand: {COLORS['primary']};",
        f"  --color-brand-alt: {COLORS['secondary']};",
        f"  --color-success: {COLORS['success']};",
        f"  --font-sans: {FONT_STACK};",
        "  --leading-display: 1.1;",
        "  --tracking-tightest: -0.02em;",
    ]
    lignes += [f"  --shadow-{nom}: {valeur};" for nom, valeur in SHADOWS.items()]
    return "@theme {\n" + "\n".join(lignes) + "\n}"
