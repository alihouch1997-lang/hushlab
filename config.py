"""Configuration lue depuis l'environnement, jamais écrite dans le code.

Aucun secret ne figure dans le dépôt : chaque valeur sensible vient d'une
variable d'environnement, avec un comportement sûr par défaut si elle manque.
"""

import os
import secrets
from pathlib import Path

RACINE = Path(__file__).parent


def _booleen(nom: str, defaut: bool = False) -> bool:
    return os.environ.get(nom, str(defaut)).lower() in {"1", "true", "oui", "yes"}


class Config:
    """Réglages de l'application. Instanciée une fois au démarrage."""

    # --- Secrets -----------------------------------------------------------
    # Sans SECRET_KEY définie, on en tire une aléatoire : les jetons CSRF
    # restent valides le temps du processus, mais ne survivent pas à un
    # redémarrage. En production, définissez-la pour de bon.
    SECRET_KEY = os.environ.get("HUSHLAB_SECRET_KEY") or secrets.token_urlsafe(32)
    SECRET_KEY_DEFINIE = bool(os.environ.get("HUSHLAB_SECRET_KEY"))
    ADMIN_MOTDEPASSE = os.environ.get("HUSHLAB_ADMIN_MOTDEPASSE")

    # --- Exécution ---------------------------------------------------------
    # Le débogueur Werkzeug permet d'exécuter du code arbitraire : il ne doit
    # jamais s'activer par accident. Il faut le demander explicitement.
    DEBUG = _booleen("HUSHLAB_DEBUG")
    PORT = int(os.environ.get("PORT", 5001))

    # Nombre de reverse proxys devant l'application.
    # 0 = aucun (défaut sûr). Une valeur trop élevée permettrait à n'importe
    # qui de falsifier son adresse IP via X-Forwarded-For, et donc de
    # contourner la limitation de débit : ne la relever qu'en connaissance
    # de l'infrastructure réelle (1 pour Render, Railway, Fly.io).
    PROXYS_DE_CONFIANCE = int(os.environ.get("HUSHLAB_PROXYS", 0))

    # --- Limites (déni de service) ----------------------------------------
    MAX_CONTENT_LENGTH = 64 * 1024          # corps de requête : 64 Ko suffisent
    LONGUEURS_MAX = {                       # par champ du formulaire
        "nom": 120, "email": 254, "telephone": 30,
        "service": 60, "message": 5000, "origine": 200,
    }
    DEMANDES_PAR_MINUTE = 5                 # par adresse IP
    ESSAIS_ADMIN_PAR_MINUTE = 5

    # --- Base de données ---------------------------------------------------
    BASE_SQLITE = Path(os.environ.get("HUSHLAB_BASE", RACINE / "hushlab.db"))

    # --- Divers ------------------------------------------------------------
    SEND_FILE_MAX_AGE_DEFAULT = 60 * 60 * 24 * 30
    FUSEAU = "Africa/Casablanca"            # affichage des dates côté admin

    # Cookies : inutilisés aujourd'hui, mais verrouillés d'avance.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _booleen("HUSHLAB_HTTPS", True)

    @classmethod
    def smtp_configure(cls) -> bool:
        return bool(os.environ.get("SMTP_HOTE"))
