"""Validation et nettoyage des données entrantes.

Principe : ne jamais faire confiance au formulaire. On borne la longueur, on
retire les caractères de contrôle, et on refuse ce qui n'a pas la forme
attendue — avant tout enregistrement et avant toute construction d'email.
"""

import re
import unicodedata

from config import Config

# Vérification pragmatique : une partie locale, une arobase, un domaine avec
# un point. Le seul test définitif reste l'envoi d'un message, mais ceci
# écarte les saisies manifestement fausses sans rejeter d'adresse légitime.
MOTIF_EMAIL = re.compile(r"^[^@\s]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MOTIF_TELEPHONE = re.compile(r"^[0-9+().\s-]{6,30}$")


def nettoyer(valeur: str, longueur_max: int) -> str:
    """Normalise une chaîne saisie par un visiteur.

    Retire les caractères de contrôle (dont les sauts de ligne, vecteur
    d'injection dans les en-têtes d'email), normalise l'Unicode et tronque.
    Les retours à la ligne sont conservés dans les champs multilignes via
    `nettoyer_multiligne`.
    """
    valeur = unicodedata.normalize("NFC", valeur or "")
    valeur = "".join(c for c in valeur if unicodedata.category(c)[0] != "C")
    return valeur.strip()[:longueur_max]


def nettoyer_multiligne(valeur: str, longueur_max: int) -> str:
    """Comme `nettoyer`, mais garde les retours à la ligne du message."""
    valeur = unicodedata.normalize("NFC", valeur or "")
    valeur = "".join(c for c in valeur
                     if c in "\n\t" or unicodedata.category(c)[0] != "C")
    return valeur.strip()[:longueur_max]


def entete_email_sur(valeur: str) -> str:
    """Chaîne utilisable dans un en-tête d'email, sans saut de ligne possible.

    Python refuse déjà les en-têtes contenant CR/LF, mais il lève alors une
    ValueError : sans ce nettoyage, un nom malformé ferait échouer la
    notification après l'enregistrement de la demande.
    """
    return re.sub(r"[\r\n]+", " ", valeur or "").strip()[:200]


def valider_demande(formulaire, services_connus: set[str]) -> tuple[dict, dict]:
    """Valide le formulaire de contact.

    Renvoie `(champs_nettoyes, erreurs)`. `erreurs` vide signifie que la
    demande peut être enregistrée telle quelle.
    """
    limites = Config.LONGUEURS_MAX
    champs = {
        "nom": nettoyer(formulaire.get("nom", ""), limites["nom"]),
        "email": nettoyer(formulaire.get("email", ""), limites["email"]).lower(),
        "telephone": nettoyer(formulaire.get("telephone", ""), limites["telephone"]),
        "service": nettoyer(formulaire.get("service", ""), limites["service"]),
        "message": nettoyer_multiligne(formulaire.get("message", ""), limites["message"]),
        "origine": nettoyer(formulaire.get("origine", "site"), limites["origine"]),
    }

    erreurs: dict[str, str] = {}
    if len(champs["nom"]) < 2:
        erreurs["nom"] = "Indiquez votre nom."
    if not MOTIF_EMAIL.match(champs["email"]):
        erreurs["email"] = "Cette adresse email ne semble pas valide."
    if champs["telephone"] and not MOTIF_TELEPHONE.match(champs["telephone"]):
        erreurs["telephone"] = "Ce numéro ne semble pas valide."
    if len(champs["message"]) < 10:
        erreurs["message"] = "Détaillez un peu votre besoin (10 caractères minimum)."

    # Un service inconnu vient forcément d'un formulaire trafiqué : on le
    # neutralise au lieu de stocker n'importe quoi.
    if champs["service"] and champs["service"] not in services_connus:
        champs["service"] = ""

    return champs, erreurs
