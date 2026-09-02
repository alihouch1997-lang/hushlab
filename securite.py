"""Couche de sécurité : en-têtes, CSRF, limitation de débit, authentification.

Les mesures suivent les recommandations OWASP applicables à un site vitrine
avec formulaire et écran d'administration :

  A01 Contrôle d'accès       → `protege` + limitation des essais
  A02 Défaillances crypto    → jetons signés, comparaison à temps constant
  A03 Injection              → requêtes paramétrées (donnees.py) + CSP
  A05 Mauvaise configuration → débogueur désactivé par défaut, en-têtes stricts
  A07 Authentification       → limitation de débit sur le mot de passe admin
"""

import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from functools import wraps

from flask import Response, abort, current_app, g, render_template, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from config import Config

# --- Limitation de débit ----------------------------------------------------
# Compteur en mémoire : suffisant pour un site servi par un seul processus.
# Derrière plusieurs workers ou plusieurs machines, il faudra un stockage
# partagé (Redis) — la limite deviendrait sinon « N fois la limite ».
_HISTORIQUE: dict[str, deque] = defaultdict(deque)
_DERNIER_MENAGE = 0.0


def reinitialiser_limites() -> None:
    """Vide les compteurs. Utilisé par les tests pour repartir d'un état neuf."""
    _HISTORIQUE.clear()


def _faire_le_menage(maintenant: float, fenetre: int) -> None:
    """Supprime les seaux vides.

    Sans cela, le dictionnaire garde une entrée par adresse IP vue depuis le
    démarrage : une fuite mémoire lente mais certaine sur un site public.
    """
    global _DERNIER_MENAGE
    if maintenant - _DERNIER_MENAGE < 300:      # au plus toutes les 5 minutes
        return
    _DERNIER_MENAGE = maintenant
    for cle in [c for c, h in _HISTORIQUE.items()
                if not h or maintenant - h[-1] > fenetre]:
        del _HISTORIQUE[cle]


def _client() -> str:
    """Adresse de l'appelant. Derrière un reverse proxy, voir ProxyFix."""
    return request.remote_addr or "inconnu"


def trop_de_requetes(seau: str, maximum: int, fenetre: int = 60) -> bool:
    """Renvoie True si l'appelant dépasse `maximum` appels dans la fenêtre."""
    cle = f"{seau}:{_client()}"
    maintenant = time.monotonic()
    _faire_le_menage(maintenant, fenetre)
    horodatages = _HISTORIQUE[cle]
    while horodatages and maintenant - horodatages[0] > fenetre:
        horodatages.popleft()
    if len(horodatages) >= maximum:
        return True
    horodatages.append(maintenant)
    return False


# --- Jetons CSRF ------------------------------------------------------------
# Deux corrections par rapport à la première version :
#
#  1. Le jeton porte une « audience ». Un jeton récolté sur la page d'accueil
#     publique ne vaut plus rien sur les routes d'administration : la signature
#     est calculée avec un sel différent.
#  2. Le contrôle anti-robot du délai de remplissage s'appuie sur l'horodatage
#     *signé* du jeton, et non plus sur un champ caché fourni par le client.
#     L'ancien champ `horodatage` était en clair : un robot le reculait de
#     quelques secondes et passait la barrière sans effort.


def _serialiseur(audience: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt=f"csrf-hushlab-{audience}")


def jeton_csrf(audience: str = "public") -> str:
    """Jeton signé et horodaté, réutilisé pour toute la requête en cours."""
    cle = f"_csrf_{audience}"
    if not hasattr(g, cle):
        setattr(g, cle, _serialiseur(audience).dumps(audience))
    return getattr(g, cle)


def verifier_csrf(audience: str = "public", *, duree_max: int = 7200,
                  delai_minimum: int = 0) -> None:
    """Refuse la requête si le jeton est absent, forgé, expiré ou trop frais.

    `delai_minimum` remplace l'ancien champ caché : un formulaire renvoyé en
    moins de N secondes après l'affichage de la page n'a pas été rempli par
    un humain. Le délai se lit dans la signature, donc il n'est pas falsifiable.
    """
    origine = request.headers.get("Origin") or request.headers.get("Referer")
    if origine and not origine.startswith(request.host_url.rstrip("/")):
        abort(403, description="Origine de la requête non autorisée.")

    jeton = request.form.get("csrf") or request.headers.get("X-CSRF-Token", "")
    try:
        _charge, emis_le = _serialiseur(audience).loads(
            jeton, max_age=duree_max, return_timestamp=True)
    except BadSignature:
        abort(403, description="Jeton de sécurité invalide ou expiré. Rechargez la page.")

    if delai_minimum:
        age = (datetime.now(timezone.utc) - emis_le).total_seconds()
        if age < delai_minimum:
            abort(403, description="Formulaire envoyé trop vite. Réessayez.")


# --- Domaine d'accès --------------------------------------------------------

def verifier_hote() -> None:
    """Refuse une requête présentant un Host non déclaré.

    Tout ce que le site construit en URL absolue — lien canonique, aperçu de
    partage, destination des QR codes, fiche schema.org — dérive de cet
    en-tête. Le laisser libre revient à laisser un tiers décider de ces URL.
    """
    if not Config.HOTES_AUTORISES:
        return                                   # développement : pas de contrainte
    hote = (request.host or "").lower().split(":")[0]
    if hote not in Config.HOTES_AUTORISES:
        # Journalisé explicitement : sans cette ligne, une liste HUSHLAB_HOTES
        # mal renseignée fait répondre 400 à tout le monde sans qu'aucun
        # message n'indique quel domaine a été refusé ni lequel était attendu.
        current_app.logger.warning(
            "Domaine refusé : %r. HUSHLAB_HOTES contient %s. "
            "Ajoutez-y ce domaine, ou videz la variable pour tout accepter.",
            hote, ", ".join(Config.HOTES_AUTORISES) or "(vide)")
        abort(400, description="Domaine d'accès non reconnu.")


# --- En-têtes de réponse ----------------------------------------------------

def nonce_csp() -> str:
    """Valeur à usage unique autorisant nos propres scripts en ligne."""
    if not hasattr(g, "_nonce"):
        g._nonce = secrets.token_urlsafe(16)
    return g._nonce


def poser_entetes(reponse: Response) -> Response:
    """Applique les en-têtes de sécurité à chaque réponse."""
    politique = (
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce_csp()}'; "
        "style-src 'self' 'unsafe-inline'; "   # classes utilitaires + <style> compilé
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "object-src 'none'"
    )
    reponse.headers.setdefault("Content-Security-Policy", politique)
    reponse.headers.setdefault("X-Content-Type-Options", "nosniff")
    reponse.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    reponse.headers.setdefault("X-Frame-Options", "DENY")
    reponse.headers.setdefault("Permissions-Policy",
                               "geolocation=(), microphone=(), camera=(), interest-cohort=()")
    if request.is_secure:
        reponse.headers.setdefault("Strict-Transport-Security",
                                   "max-age=31536000; includeSubDomains")
    # Les pages d'administration contiennent des données clients : aucun cache.
    if request.path.startswith("/admin"):
        reponse.headers["Cache-Control"] = "no-store, private"
    return reponse


# --- Authentification de l'administration -----------------------------------

def protege(vue):
    """Exige le mot de passe d'administration, avec limitation des essais.

    Tant que HUSHLAB_ADMIN_MOTDEPASSE n'est pas définie, l'écran reste fermé :
    aucune administration n'est joignable par défaut.
    """
    @wraps(vue)
    def enveloppe(*args, **kwargs):
        attendu = Config.ADMIN_MOTDEPASSE
        if not attendu:
            return render_template("admin_ferme.html"), 503

        auth = request.authorization
        fourni = auth.password if auth and auth.password else ""

        # Le compteur ne s'incrémente que sur échec : un usage normal n'est
        # jamais bridé, une attaque par dictionnaire l'est au bout de 5 essais.
        if secrets.compare_digest(fourni, attendu):
            return vue(*args, **kwargs)

        if trop_de_requetes("admin", Config.ESSAIS_ADMIN_PAR_MINUTE):
            abort(429, description="Trop de tentatives. Réessayez dans une minute.")

        return Response(
            "Accès réservé", 401,
            {"WWW-Authenticate": 'Basic realm="Administration Hushlab"'})
    return enveloppe
