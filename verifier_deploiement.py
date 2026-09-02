#!/usr/bin/env python
"""Diagnostic de déploiement : dit en une commande ce qui bloque.

    python3 verifier_deploiement.py

Chaque contrôle correspond à une panne réellement rencontrée en mettant ce
site en ligne. Le script s'arrête au premier problème bloquant et indique la
correction, plutôt que de laisser lire un journal d'erreurs.
"""

import os
import sys
from pathlib import Path

RACINE = Path(__file__).parent
VERSION_MINIMALE = (3, 10)
ok, problemes = [], []


def controle(intitule: str, reussi: bool, remede: str = "") -> bool:
    (ok if reussi else problemes).append((intitule, remede))
    print(f"  {'✓' if reussi else '✗'}  {intitule}")
    if not reussi and remede:
        print(f"      → {remede}")
    return reussi


print("\n=== Version de Python ===")
actuelle = sys.version_info[:2]
if not controle(
        f"Python {actuelle[0]}.{actuelle[1]} (minimum {'.'.join(map(str, VERSION_MINIMALE))})",
        actuelle >= VERSION_MINIMALE,
        "Flask 3 exige Python 3.9 et ce site 3.10. Sur PythonAnywhere, la "
        "version d'une application web ne se change pas : supprimez-la et "
        "recréez-la avec une version récente."):
    print("\nInutile de poursuivre : les contrôles suivants échoueraient tous.\n")
    sys.exit(1)

print("\n=== Dépendances ===")
for module, remede in [
        ("flask", "pip install -r requirements.txt, dans le virtualenv actif"),
        ("qrcode", "pip install -r requirements.txt, dans le virtualenv actif")]:
    try:
        __import__(module)
        controle(f"{module} installé", True)
    except ImportError:
        controle(f"{module} installé", False, remede)

print("\n=== Fichiers du projet ===")
for chemin, remede in [
        ("app.py", "le clonage a échoué : refaites git clone"),
        ("icons.json", "fichier manquant : git pull"),
        ("static/css/app.css", "feuille de style absente : git pull"),
        ("templates/base.html", "gabarits absents : git pull")]:
    controle(chemin, (RACINE / chemin).is_file(), remede)

print("\n=== Écriture de la base de données ===")
try:
    essai = RACINE / ".essai_ecriture"
    essai.write_text("x", encoding="utf-8")
    essai.unlink()
    controle("dossier accessible en écriture", True)
except OSError as erreur:
    controle("dossier accessible en écriture", False,
             f"{erreur} — la base de données ne pourra pas être créée")

print("\n=== Réglages ===")
controle("HUSHLAB_SECRET_KEY définie", bool(os.environ.get("HUSHLAB_SECRET_KEY")),
         "sans elle, une clé aléatoire est tirée à chaque redémarrage et les "
         "formulaires ouverts échouent. À placer dans le fichier .env")
controle("HUSHLAB_DEBUG désactivé", os.environ.get("HUSHLAB_DEBUG", "0") not in {"1", "true"},
         "DANGER : le débogueur permet d'exécuter du code à distance")
hotes = os.environ.get("HUSHLAB_HOTES", "")
controle(f"HUSHLAB_HOTES = {hotes or '(vide, tous domaines acceptés)'}", True)

print("\n=== Démarrage de l'application ===")
try:
    sys.path.insert(0, str(RACINE))
    from app import app
    reponse = app.test_client().get("/")
    controle(f"la page d'accueil répond ({reponse.status_code})", reponse.status_code == 200,
             "le site démarre mais renvoie une erreur : voir le message ci-dessus")
except Exception as erreur:
    controle("l'application démarre", False, f"{type(erreur).__name__} : {erreur}")

print()
if problemes:
    print(f"{len(problemes)} problème(s) à corriger, listé(s) ci-dessus.\n")
    sys.exit(1)
print("Tout est en ordre. Cliquez sur « Reload » dans l'onglet Web.\n")
