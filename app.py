"""Site vitrine Hushlab — application Flask.

Organisation des modules
------------------------
config.py        réglages, lus dans l'environnement (aucun secret en dur)
securite.py      en-têtes, CSRF, limitation de débit, authentification admin
validation.py    nettoyage et contrôle des données entrantes
donnees.py       accès SQLite (demandes clients, scans de QR codes)
contenu.py       texte publié : services, offres, articles, coordonnées
design_tokens.py tokens du design system, compilés par build.py
app.py           fabrique de l'application, routes et rendu

Lancement en développement :
    HUSHLAB_DEBUG=1 .venv/bin/python app.py
En production, servir `app` derrière gunicorn ou waitress — jamais avec le
serveur de développement de Flask.
"""

import io
import json
import logging
import pathlib
from functools import lru_cache

import qrcode
import qrcode.image.svg
from flask import Flask, Response, abort, redirect, render_template, request, url_for
from markupsafe import Markup, escape

import contenu
import design_tokens
import donnees
import securite
import validation
from config import Config

# --------------------------------------------------------------------------- #
# Fabrique de l'application
# --------------------------------------------------------------------------- #

app = Flask(__name__)
app.config.from_object(Config)
donnees.initialiser()

if not Config.SECRET_KEY_DEFINIE:
    logging.getLogger(__name__).warning(
        "HUSHLAB_SECRET_KEY n'est pas définie : une clé aléatoire est utilisée. "
        "Les jetons CSRF seront invalidés à chaque redémarrage.")

# Tracés SVG figés par build.py : le visiteur ne charge plus les 97 Ko de
# JavaScript de lucide, les icônes arrivent directement dans le HTML.
ICONES: dict[str, str] = json.loads(
    (pathlib.Path(app.root_path) / "icons.json").read_text(encoding="utf-8"))

SLUGS_SERVICES = {service["slug"] for service in contenu.SERVICES}


@app.after_request
def _securiser(reponse: Response) -> Response:
    return securite.poser_entetes(reponse)


# --------------------------------------------------------------------------- #
# Fonctions disponibles dans les templates
# --------------------------------------------------------------------------- #

@app.template_global()
def icone(nom: str, classes: str = "h-5 w-5") -> Markup:
    """Rend une icône en SVG inline.

    `classes` est échappé : la fonction reste sûre même si un appelant futur
    y fait passer une valeur venue de l'extérieur. Un nom d'icône inconnu
    échoue bruyamment en développement, silencieusement en production.
    """
    corps = ICONES.get(nom)
    if corps is None:
        if app.debug:
            raise KeyError(f"Icône inconnue : {nom!r}. Ajoutez-la dans icons.json.")
        app.logger.warning("Icône manquante : %s", nom)
        return Markup("")
    return Markup(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" class="{escape(classes)}" aria-hidden="true">{corps}</svg>'
    )


@app.template_global()
def date_locale(horodatage: str) -> str:
    """Affiche un horodatage UTC à l'heure de Rabat."""
    return donnees.en_heure_locale(horodatage)


# --------------------------------------------------------------------------- #
# Helpers de contenu
# --------------------------------------------------------------------------- #

def _href(element: dict) -> str:
    """Résout un lien déclaré en endpoint + ancre, ou renvoie son href direct."""
    if element.get("href"):
        return element["href"]
    if not element.get("endpoint"):
        return "#"
    ancre = f"#{element['anchor']}" if element.get("anchor") else ""
    return url_for(element["endpoint"]) + ancre


def _resoudre(elements: list[dict]) -> list[dict]:
    return [dict(element, href=_href(element)) for element in elements]


def article_par_slug(slug: str) -> dict | None:
    return next((a for a in contenu.ARTICLES if a["slug"] == slug), None)


def qr_par_code(code: str) -> dict | None:
    return next((q for q in contenu.QR_CODES if q["code"] == code), None)


# --------------------------------------------------------------------------- #
# Données structurées (schema.org)
# --------------------------------------------------------------------------- #

def fiche_entreprise() -> dict:
    """Fiche LocalBusiness lue par Google pour l'affichage enrichi."""
    site = contenu.SITE
    racine = request.url_root.rstrip("/")
    return {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": site["name"],
        "description": contenu.META_DEFAUT["description"],
        "url": racine,
        "image": racine + url_for("static", filename="img/og.jpg"),
        "telephone": site["phone_link"],
        "email": site["email"],
        "founder": {"@type": "Person", "name": site["founder"]},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": site["address"],
            "addressLocality": site["city"].split(",")[0].strip(),
            "addressCountry": "MA",
        },
        "areaServed": {"@type": "Country", "name": "Maroc"},
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday",
                          "Thursday", "Friday", "Saturday"],
            "opens": "09:00", "closes": "19:00",
        }],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": f"Services {site['name']}",
            "itemListElement": [
                {"@type": "Offer",
                 "itemOffered": {"@type": "Service", "name": service["title"],
                                 "description": service["body"]}}
                for service in contenu.SERVICES
            ],
        },
    }


def fiche_article(billet: dict) -> dict:
    """Fiche Article : affichage enrichi des billets dans les résultats."""
    racine = request.url_root.rstrip("/")
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": billet["title"],
        "description": billet["excerpt"],
        "datePublished": billet["date_iso"],
        "image": racine + url_for("static", filename="img/" + billet["image"]),
        "author": {"@type": "Person", "name": contenu.SITE["founder"]},
        "publisher": {"@type": "Organization", "name": contenu.SITE["name"]},
        "mainEntityOfPage": racine + url_for("article", slug=billet["slug"]),
    }


# --------------------------------------------------------------------------- #
# Notification par email
# --------------------------------------------------------------------------- #

def notifier_par_email(demande: dict) -> bool:
    """Prévient Hushlab d'une nouvelle demande, si le SMTP est configuré.

    Toute la fonction est protégée : un échec d'envoi, un serveur injoignable
    ou un en-tête refusé ne doivent jamais faire échouer la requête HTTP —
    la demande est déjà enregistrée en base à ce stade.

    Variables attendues : SMTP_HOTE, SMTP_PORT, SMTP_UTILISATEUR,
    SMTP_MOTDEPASSE, SMTP_DESTINATAIRE.
    """
    import os
    import smtplib
    from email.message import EmailMessage

    hote = os.environ.get("SMTP_HOTE")
    if not hote:
        return False

    try:
        message = EmailMessage()
        message["Subject"] = validation.entete_email_sur(
            f"Nouvelle demande — {demande['nom']}")
        message["From"] = os.environ.get("SMTP_UTILISATEUR", contenu.SITE["email"])
        message["To"] = os.environ.get("SMTP_DESTINATAIRE", contenu.SITE["email"])
        message["Reply-To"] = validation.entete_email_sur(demande["email"])
        message.set_content(
            f"Nom       : {demande['nom']}\n"
            f"Email     : {demande['email']}\n"
            f"Téléphone : {demande['telephone'] or '—'}\n"
            f"Service   : {demande['service'] or '—'}\n\n"
            f"{demande['message']}\n"
        )
        with smtplib.SMTP(hote, int(os.environ.get("SMTP_PORT", 587)),
                          timeout=10) as serveur:
            serveur.starttls()
            if os.environ.get("SMTP_MOTDEPASSE"):
                serveur.login(os.environ["SMTP_UTILISATEUR"],
                              os.environ["SMTP_MOTDEPASSE"])
            serveur.send_message(message)
        return True
    except Exception:
        app.logger.exception("Notification email impossible")
        return False


# --------------------------------------------------------------------------- #
# QR codes
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=32)
def _qr_svg(contenu_encode: str) -> bytes:
    """Génère le SVG d'un QR code. Le résultat est déterministe, donc mis en cache."""
    image = qrcode.make(contenu_encode, image_factory=qrcode.image.svg.SvgPathImage,
                        box_size=12, border=2)
    tampon = io.BytesIO()
    image.save(tampon)
    return tampon.getvalue()


def _reponse_qr(contenu_encode: str) -> Response:
    return Response(_qr_svg(contenu_encode), mimetype="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


def vcard() -> str:
    """Fiche contact au format vCard, encodée dans le QR de la page contact."""
    site = contenu.SITE
    prenom, *_, nom_famille = site["founder"].split()
    return "\r\n".join([
        "BEGIN:VCARD", "VERSION:3.0",
        f"N:{nom_famille};{prenom}",
        f"FN:{site['founder']}",
        f"ORG:{site['name']}",
        f"TITLE:{site['founder_role']}",
        f"TEL;TYPE=CELL:{site['phone_link']}",
        f"EMAIL:{site['email']}",
        f"ADR;TYPE=WORK:;;{site['address']};{site['city'].split(',')[0]};;;Maroc",
        "END:VCARD",
    ])


# --------------------------------------------------------------------------- #
# Injection globale dans les templates
# --------------------------------------------------------------------------- #

@app.context_processor
def _contexte_global() -> dict:
    return {
        "site": contenu.SITE,
        "nav": _resoudre(contenu.NAV),
        "footer_columns": [dict(colonne, links=_resoudre(colonne["links"]))
                           for colonne in contenu.FOOTER_COLUMNS],
        "sections": contenu.SECTIONS,
        "socials": contenu.SOCIALS,
        "gradient": design_tokens.GRADIENT,
        "meta": contenu.META_DEFAUT,
        "donnees_structurees": fiche_entreprise(),
        "csrf": securite.jeton_csrf,
        "nonce": securite.nonce_csp,
    }


# --------------------------------------------------------------------------- #
# Pages publiques
# --------------------------------------------------------------------------- #

def _accueil(**extra):
    """Rend la page d'accueil ; `extra` transporte l'état du formulaire."""
    import time
    return render_template(
        "index.html",
        hero=contenu.HERO,
        engagements=contenu.ENGAGEMENTS,
        services=contenu.SERVICES,
        methode=contenu.METHODE,
        fondateur=contenu.FONDATEUR,
        offres=contenu.OFFRES,
        offres_note=contenu.OFFRES_NOTE,
        temoignages=contenu.TEMOIGNAGES,
        articles=contenu.ARTICLES[:3],
        faq=contenu.FAQ,
        contacts=contenu.CONTACTS,
        qr_codes=contenu.QR_CODES,
        horodatage=int(time.time()),
        **extra,
    )


@app.route("/")
def accueil():
    return _accueil()


@app.route("/blog")
def blog():
    return render_template(
        "blog.html",
        articles=contenu.ARTICLES,
        categories=sorted({a["category"] for a in contenu.ARTICLES}),
        meta=dict(contenu.META_DEFAUT,
                  titre=f"Blog — {contenu.SITE['name']}",
                  description="Nos retours d'expérience sur les sites web, les QR "
                              "codes, les réseaux sociaux, l'IA et la création "
                              "d'entreprise."),
    )


@app.route("/blog/<slug>")
def article(slug: str):
    billet = article_par_slug(slug)
    if billet is None:
        abort(404)
    suggestions = [a for a in contenu.ARTICLES if a["slug"] != slug][:2]
    return render_template(
        "article.html", article=billet, suggestions=suggestions,
        meta=dict(contenu.META_DEFAUT,
                  titre=f"{billet['title']} — {contenu.SITE['name']}",
                  description=billet["excerpt"],
                  image="img/" + billet["image"],
                  type="article"),
        donnees_article=fiche_article(billet),
    )


@app.route("/qr/contact.svg")
def qr_contact():
    """Scanné, ce QR enregistre la fiche contact Hushlab dans le téléphone."""
    return _reponse_qr(vcard())


@app.route("/qr/<code>.svg")
def qr_suivi(code: str):
    """QR pointant vers /r/<code>, ce qui permet d'en compter les scans."""
    if qr_par_code(code) is None:
        abort(404)
    return _reponse_qr(request.url_root.rstrip("/") + url_for("redirection", code=code))


@app.route("/r/<code>")
def redirection(code: str):
    """Compte le scan puis renvoie vers la destination du QR.

    La destination vient d'une liste fermée définie dans contenu.py : aucune
    URL fournie par l'appelant n'est suivie, ce qui écarte la redirection
    ouverte et le SSRF.
    """
    entree = qr_par_code(code)
    if entree is None:
        abort(404)
    try:
        donnees.enregistrer_scan(code)
    except Exception:
        # Un compteur en échec ne doit pas empêcher le client d'arriver à
        # destination : on trace et on redirige quand même.
        app.logger.exception("Scan non comptabilisé pour %s", code)
    cible = entree["cible"]
    return redirect(url_for("accueil") if cible == "/" else cible, code=302)


@app.route("/contact", methods=["POST"])
def contact():
    """Enregistre une demande, puis prévient Hushlab par email.

    Trois barrières successives : jeton CSRF, limitation de débit par IP,
    puis piège à robots (champ leurre et délai minimal de remplissage).
    """
    securite.verifier_csrf()

    if securite.trop_de_requetes("contact", Config.DEMANDES_PAR_MINUTE):
        abort(429, description="Trop de demandes envoyées. Réessayez dans une minute.")

    # Leurre rempli, ou formulaire renvoyé en moins de deux secondes : on
    # répond comme si tout allait bien, sans rien enregistrer.
    import time
    depart = request.form.get("horodatage", "0")
    trop_rapide = not depart.isdigit() or time.time() - int(depart) < 2
    if request.form.get("site_web") or trop_rapide:
        app.logger.info("Envoi automatisé ignoré")
        return redirect(url_for("accueil", envoye=1) + "#contact")

    champs, erreurs = validation.valider_demande(request.form, SLUGS_SERVICES)
    if erreurs:
        return _accueil(erreurs=erreurs, valeurs=champs), 400

    identifiant = donnees.enregistrer_demande(**champs)
    notifier_par_email(champs)
    app.logger.info("Demande #%s enregistrée", identifiant)  # sans donnée personnelle
    return redirect(url_for("accueil", envoye=1) + "#contact")


# --------------------------------------------------------------------------- #
# Référencement
# --------------------------------------------------------------------------- #

@app.route("/sitemap.xml")
def sitemap():
    """Plan du site, construit depuis les données de contenu.py."""
    racine = request.url_root.rstrip("/")
    pages = [(racine + url_for("accueil"), None, "1.0"),
             (racine + url_for("blog"), None, "0.8")]
    pages += [(racine + url_for("article", slug=a["slug"]), a["date_iso"], "0.6")
              for a in contenu.ARTICLES]

    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for adresse, date, priorite in pages:
        lignes.append("  <url>")
        lignes.append(f"    <loc>{escape(adresse)}</loc>")
        if date:
            lignes.append(f"    <lastmod>{date}</lastmod>")
        lignes.append(f"    <priority>{priorite}</priority>")
        lignes.append("  </url>")
    lignes.append("</urlset>")
    return Response("\n".join(lignes), mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    racine = request.url_root.rstrip("/")
    return Response(
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        f"Sitemap: {racine}/sitemap.xml\n",
        mimetype="text/plain")


# --------------------------------------------------------------------------- #
# Administration
# --------------------------------------------------------------------------- #

@app.route("/admin")
@securite.protege
def admin():
    tableau = donnees.tableau_de_bord()
    return render_template(
        "admin.html",
        demandes=tableau["demandes"],
        compteurs=tableau["compteurs"],
        scans=tableau["scans"],
        qr_codes=contenu.QR_CODES,
        libelles_services={s["slug"]: s["title"] for s in contenu.SERVICES},
        smtp_actif=Config.smtp_configure(),
    )


@app.route("/admin/demande/<int:identifiant>/<statut>", methods=["POST"])
@securite.protege
def admin_statut(identifiant: int, statut: str):
    securite.verifier_csrf()
    if statut not in {"nouveau", "traite"}:
        abort(400, description="Statut inconnu.")
    if not donnees.changer_statut(identifiant, statut):
        abort(404, description="Cette demande n'existe pas.")
    return redirect(url_for("admin"))


@app.route("/admin/export.csv")
@securite.protege
def admin_export():
    return Response(
        donnees.exporter_csv(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=demandes-hushlab.csv"},
    )


# --------------------------------------------------------------------------- #
# Erreurs — une page lisible plutôt qu'une trace technique
# --------------------------------------------------------------------------- #

def _page_erreur(code: int, titre: str, explication: str):
    return render_template("erreur.html", code=code, titre=titre,
                           explication=explication), code


@app.errorhandler(400)
def _erreur_400(erreur):
    return _page_erreur(400, "Demande incorrecte",
                        getattr(erreur, "description", "La requête n'a pas pu être lue."))


@app.errorhandler(403)
def _erreur_403(erreur):
    return _page_erreur(403, "Requête refusée",
                        getattr(erreur, "description",
                                "Votre session a expiré. Rechargez la page et réessayez."))


@app.errorhandler(404)
def _erreur_404(_):
    return render_template("404.html"), 404


@app.errorhandler(413)
def _erreur_413(_):
    return _page_erreur(413, "Message trop volumineux",
                        "Votre message dépasse la taille acceptée. Raccourcissez-le.")


@app.errorhandler(429)
def _erreur_429(erreur):
    return _page_erreur(429, "Trop de requêtes",
                        getattr(erreur, "description", "Patientez une minute."))


@app.errorhandler(500)
def _erreur_500(erreur):
    app.logger.exception("Erreur interne", exc_info=erreur)
    return _page_erreur(500, "Une erreur est survenue",
                        "Le problème a été enregistré. Écrivez-nous si cela persiste.")


if __name__ == "__main__":
    # Le débogueur Werkzeug exécute du code arbitraire : il ne s'active que si
    # HUSHLAB_DEBUG=1 est demandé explicitement, jamais par défaut.
    app.run(debug=Config.DEBUG, port=Config.PORT)
