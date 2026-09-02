"""Fichier WSGI prêt à copier pour PythonAnywhere.

Copiez le contenu de ce fichier dans le « WSGI configuration file » de
l'onglet Web, et remplacez UNIQUEMENT le nom d'utilisateur ci-dessous.

Aucun secret ici : ils vivent dans le fichier .env du projet, ce qui évite
de les recopier à la main dans une interface web.
"""

import sys

UTILISATEUR = "hvshbar"          # ← la seule ligne à adapter

CHEMIN = f"/home/{UTILISATEUR}/hushlab"
if CHEMIN not in sys.path:
    sys.path.insert(0, CHEMIN)

from app import app as application  # noqa: E402
