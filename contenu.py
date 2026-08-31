"""Contenu éditorial du site Hushlab.

Tout le texte publié vit ici, séparé du code applicatif : modifier une offre,
un article ou un horaire ne demande d'ouvrir aucun fichier de logique. Les
templates ne portent que la mise en forme.

Ce module est volontairement sans dépendance : il ne fait qu'exposer des
données, ce qui le rend trivialement testable et réutilisable (génération de
flux RSS, export, version arabe à venir).
"""

SITE = {
    "name": "Hushlab",
    "baseline": "Vos projets avancent, on s'occupe du reste.",
    "founder": "Ali Houch",
    "founder_role": "Fondateur",
    "founder_initials": "AH",
    "email": "Hpeaky47@gmail.com",
    "phone_display": "06 56 18 54 14",
    "phone_link": "+212656185414",
    "whatsapp": "https://wa.me/212656185414",
    "address": "7 rue Ghinia, Diour Jamaa",
    "city": "Rabat, Maroc",
    "hours": "Du lundi au samedi, 9 h – 19 h",
}

# La nav est déclarée en endpoints + ancres : les liens restent valides
# depuis n'importe quelle page (accueil, blog, article).
NAV = [
    {"label": "Services", "endpoint": "accueil", "anchor": "services"},
    {"label": "Méthode", "endpoint": "accueil", "anchor": "methode"},
    {"label": "Offres", "endpoint": "accueil", "anchor": "offres"},
    {"label": "Blog", "endpoint": "blog"},
    {"label": "Contact", "endpoint": "accueil", "anchor": "contact"},
]

HERO = {
    "badge": "NOUVEAU",
    "badge_text": "Hushlab accompagne les entreprises à Rabat",
    # Le titre est coupé en deux : la seconde moitié reçoit le dégradé.
    "title_plain": "Vos projets avancent,",
    "title_gradient": "on s'occupe du reste",
    "body": (
        "Sites web, QR et NFC, réseaux sociaux, intelligence artificielle, "
        "création d'entreprise de A à Z. Un seul interlocuteur pour des "
        "métiers que vous confiez d'habitude à quatre prestataires."
    ),
    "primary_cta": "Parler de mon projet",
    "secondary_cta": "Voir les services",
    "proof": "Premier échange gratuit · Réponse sous 24 h · Basés à Rabat",
    "image": "hero-equipe.jpg",
    "image_alt": "Une équipe réunie autour d'une table de travail",
}

ENGAGEMENTS = [
    {"value": "6", "label": "domaines couverts"},
    {"value": "A → Z", "label": "juridique et administratif"},
    {"value": "24 h", "label": "pour vous répondre"},
    {"value": "Rabat", "label": "et partout au Maroc"},
]

SERVICES = [
    {
        "slug": "sites-web",
        "icon": "globe",
        "title": "Création de sites web",
        "body": (
            "Un site qui dit clairement ce que vous faites et qui donne envie "
            "de vous contacter. Pages d'accueil, pages de services, site vitrine complet."
        ),
        "bullets": [
            "Site vitrine et pages de services",
            "Rédaction et mise en page des contenus",
            "Affichage soigné sur mobile",
            "Nom de domaine et mise en ligne",
        ],
        "image": "service-sites-web.jpg",
        "image_alt": "Ordinateur portable affichant un tableau de bord",
    },
    {
        "slug": "qr-nfc",
        "icon": "qr-code",
        "title": "QR codes et supports NFC",
        "body": (
            "Un support à scanner qui envoie vos clients au bon endroit : "
            "avis Google, Instagram, Facebook, menu du jour ou page de contact."
        ),
        "bullets": [
            "Avis Google, Instagram, Facebook",
            "Menus modifiables sans réimpression",
            "Cartes et supports NFC à poser sur table",
            "Pages d'accueil et de contact dédiées",
        ],
        "image": "service-qr-nfc.jpg",
        "image_alt": "Main tenant un smartphone",
    },
    {
        "slug": "reseaux-sociaux",
        "icon": "megaphone",
        "title": "Gestion des réseaux sociaux",
        "body": (
            "Votre page reste vivante même les semaines où vous n'avez pas le "
            "temps : publications régulières, visuels cohérents, messages traités."
        ),
        "bullets": [
            "Calendrier de publication",
            "Création des visuels et des textes",
            "Réponses aux messages et commentaires",
            "Point mensuel sur ce qui a marché",
        ],
        "image": "service-reseaux-sociaux.jpg",
        "image_alt": "Icônes d'applications sur un écran de smartphone",
    },
    {
        "slug": "intelligence-artificielle",
        "icon": "sparkles",
        "title": "Accompagnement à l'intelligence artificielle",
        "body": (
            "On repère les tâches où l'IA vous fait vraiment gagner du temps, "
            "on met les outils en place, et on reste le temps que ça devienne un réflexe."
        ),
        "bullets": [
            "Repérage des tâches répétitives",
            "Choix et mise en place des outils",
            "Modèles prêts à l'emploi pour votre métier",
            "Accompagnement dans la durée",
        ],
        "image": "service-ia.jpg",
        "image_alt": "Illustration lumineuse d'un cerveau",
    },
    {
        "slug": "formations",
        "icon": "graduation-cap",
        "title": "Formations IA pour comptables et gestionnaires",
        "body": (
            "Des sessions concrètes, construites sur vos dossiers réels plutôt "
            "que sur des exemples théoriques. Saisie, relances, reporting, courriers."
        ),
        "bullets": [
            "En présentiel ou à distance",
            "Cas pratiques tirés de vos propres dossiers",
            "Supports à garder après la session",
            "Aucun prérequis technique",
        ],
        "image": "service-formation.jpg",
        "image_alt": "Mains sur une calculatrice à côté d'un ordinateur portable",
    },
    {
        "slug": "creation-entreprise",
        "icon": "building-2",
        "title": "Création d'entreprise de A à Z",
        "body": (
            "Vous décidez de vous lancer, on prend en charge le parcours "
            "juridique et administratif jusqu'à ce que la société existe."
        ),
        "bullets": [
            "Choix de la forme juridique",
            "Rédaction et dépôt des statuts",
            "Immatriculation et enregistrements",
            "Démarches administratives et fiscales",
        ],
        "image": "service-creation-entreprise.jpg",
        "image_alt": "Document de plan d'affaires posé sur un bureau",
    },
]

METHODE = [
    {
        "icon": "phone-call",
        "title": "On échange",
        "body": "Un appel ou un café pour comprendre votre activité, votre urgence "
                "et votre budget. Gratuit, sans engagement.",
    },
    {
        "icon": "file-text",
        "title": "On cadre",
        "body": "Vous recevez une proposition écrite : ce qui est inclus, le délai, "
                "le prix. Pas de zone grise, pas de surprise en fin de projet.",
    },
    {
        "icon": "wrench",
        "title": "On réalise",
        "body": "Vous suivez l'avancement et validez à chaque étape. Rien n'est "
                "livré sans que vous l'ayez vu.",
    },
    {
        "icon": "life-buoy",
        "title": "On reste",
        "body": "Après la livraison, les corrections sont assurées et vos questions "
                "trouvent une réponse. On ne disparaît pas.",
    },
]

FONDATEUR = {
    "text": (
        "Hushlab réunit sous un même toit des métiers que les dirigeants confient "
        "d'ordinaire à plusieurs prestataires : le web, la communication, "
        "l'intelligence artificielle et les démarches de création d'entreprise. "
        "Un seul interlocuteur, une seule proposition, un seul suivi."
    ),
    "image": "methode-accompagnement.jpg",
    "image_alt": "Poignée de main au-dessus d'une table de réunion",
}

# Les tarifs se fixent après un échange : aucune grille chiffrée n'est affichée
# tant que vous ne l'avez pas arrêtée vous-même.
OFFRES = [
    {
        "name": "Présence",
        "price": "Sur devis",
        "period": "forfait unique",
        "pitch": "Pour exister en ligne proprement, sans tout construire d'un coup.",
        "features": [
            "Site vitrine ou page de services",
            "QR code avis Google",
            "Nom de domaine et mise en ligne",
            "Une session de prise en main",
        ],
        "cta": "Demander un devis",
        "featured": False,
    },
    {
        "name": "Visibilité",
        "price": "Sur devis",
        "period": "forfait + suivi mensuel",
        "pitch": "Le site, les supports à scanner et les réseaux, gérés ensemble.",
        "features": [
            "Tout ce que comprend Présence",
            "Gestion des réseaux sociaux",
            "Supports QR et NFC pour vos avis et menus",
            "Point mensuel et ajustements",
        ],
        "cta": "Demander un devis",
        "featured": True,
        "badge": "Le plus demandé",
    },
    {
        "name": "Lancement complet",
        "price": "Sur devis",
        "period": "accompagnement global",
        "pitch": "De la création de la société à sa présence en ligne.",
        "features": [
            "Création d'entreprise de A à Z",
            "Site web et supports de communication",
            "Accompagnement à l'intelligence artificielle",
            "Formation de vos équipes",
        ],
        "cta": "Parler du projet",
        "featured": False,
    },
]

OFFRES_NOTE = (
    "Les prix dépendent du nombre de pages, de la fréquence de publication et "
    "des démarches à couvrir. Ils sont fixés par écrit avant de commencer."
)

# Aucun témoignage inventé : la section apparaît dès que cette liste contient
# un avis réel. Format attendu :
#   {"quote": "…", "name": "…", "role": "…", "company": "…",
#    "initials": "…", "rating": 5, "metric": "…", "featured": True}
TEMOIGNAGES = []

ARTICLES = [
    {
        "slug": "menu-qr-restaurant",
        "title": "Le menu QR : ce que ça change vraiment pour un restaurant",
        "excerpt": (
            "Changer un prix sans réimprimer, retirer un plat en rupture à midi : "
            "l'intérêt du menu à scanner n'est pas là où on le croit."
        ),
        "category": "QR & NFC",
        "date": "20 août 2026",
        "date_iso": "2026-08-20",
        "read_time": "5 min",
        "image": "blog-menus.jpg",
        "image_alt": "Devanture de restaurant avec un menu écrit à la main",
        "body": [
            {"type": "p", "text": "Le menu à scanner a mauvaise presse depuis l'époque où il était imposé partout. Pourtant, remis à sa place, c'est un outil de gestion avant d'être un gadget : il vous rend le droit de changer d'avis."},
            {"type": "h3", "text": "Le vrai gain : la mise à jour"},
            {"type": "p", "text": "Un plat en rupture à midi disparaît de la carte en quelques secondes. Un prix qui bouge ne coûte plus une réimpression. Une suggestion du jour s'ajoute le matin même. C'est là que le menu numérique se rentabilise, pas dans la modernité affichée."},
            {"type": "quote", "text": "Un menu qu'on ne peut pas corriger avant la prochaine impression est un menu qui ment une partie de l'année."},
            {"type": "h3", "text": "Garder le papier"},
            {"type": "p", "text": "Le meilleur montage garde une carte papier pour la salle et réserve le QR à ce qui bouge : plats du jour, boissons de saison, formules du midi. Le client choisit son support, vous gardez la main sur les changements."},
            {"type": "h3", "text": "Une seule destination, bien choisie"},
            {"type": "p", "text": "Un QR qui ouvre un PDF illisible sur téléphone fait plus de mal que de bien. La page qu'il ouvre doit être pensée pour un écran tenu à une main, dans une salle éclairée à moitié."},
        ],
    },
    {
        "slug": "avis-google-sans-harceler",
        "title": "Obtenir plus d'avis Google sans harceler vos clients",
        "excerpt": (
            "La difficulté n'est pas de demander un avis, c'est de le demander "
            "au moment où le client a envie de le donner."
        ),
        "category": "Visibilité",
        "date": "6 août 2026",
        "date_iso": "2026-08-06",
        "read_time": "4 min",
        "image": "blog-reseaux.jpg",
        "image_alt": "Lettres de Scrabble formant les mots social media",
        "body": [
            {"type": "p", "text": "Les avis Google pèsent lourd dans la décision d'un client qui ne vous connaît pas. La plupart des commerces le savent, et pourtant très peu en collectent régulièrement. La raison est presque toujours la même : personne n'ose demander."},
            {"type": "h3", "text": "Demander au bon moment"},
            {"type": "p", "text": "Un avis se donne dans les minutes qui suivent une bonne expérience, rarement le lendemain. C'est pour cela qu'un support posé sur la table, sur le comptoir ou glissé avec l'addition fonctionne mieux qu'un message envoyé plus tard."},
            {"type": "h3", "text": "Enlever les étapes"},
            {"type": "p", "text": "Chaque geste supplémentaire fait perdre des clients en route : chercher le nom de l'établissement, trouver le bon bouton, se connecter. Un QR qui ouvre directement le formulaire d'avis supprime ces étapes."},
            {"type": "quote", "text": "Un client satisfait ne refuse pas de laisser un avis : il renonce en cours de route."},
            {"type": "h3", "text": "Répondre, toujours"},
            {"type": "p", "text": "Répondre aux avis — y compris aux mauvais, surtout aux mauvais — montre aux lecteurs suivants que quelqu'un s'occupe de l'endroit. C'est souvent plus convaincant que la note elle-même."},
        ],
    },
    {
        "slug": "ia-taches-comptables",
        "title": "Trois tâches que l'IA fait déjà très bien pour un comptable",
        "excerpt": (
            "Ni magie ni remplacement : trois usages concrets, testables cette "
            "semaine, sur des tâches que personne n'aime faire."
        ),
        "category": "Intelligence artificielle",
        "date": "23 juillet 2026",
        "date_iso": "2026-07-23",
        "read_time": "6 min",
        "image": "blog-comptabilite.jpg",
        "image_alt": "Carnet ouvert et calculatrice sur un bureau",
        "body": [
            {"type": "p", "text": "La question posée en formation n'est jamais « est-ce que l'IA va me remplacer ». C'est « par où je commence sans y passer mes soirées ». Voici trois entrées où le retour est immédiat."},
            {"type": "h3", "text": "1. Les courriers et les relances"},
            {"type": "p", "text": "Relance d'une pièce manquante, explication d'un écart à un client, mot d'accompagnement d'un bilan : ce sont des textes qu'on réécrit dix fois par mois. Un modèle bien construit les produit en quelques secondes, à vous de relire et d'ajuster le ton."},
            {"type": "h3", "text": "2. Le résumé de documents longs"},
            {"type": "p", "text": "Un bail, un contrat, une liasse : demander les points saillants avant de lire en détail fait gagner un temps réel. Le principe reste le même que pour un stagiaire : on vérifie ce qui est rendu."},
            {"type": "quote", "text": "L'IA ne remplace pas la vérification, elle déplace le travail vers la vérification."},
            {"type": "h3", "text": "3. Les explications au client"},
            {"type": "p", "text": "Traduire un mécanisme fiscal en langage clair, pour un dirigeant qui n'est pas comptable, est une compétence à part entière. C'est précisément ce que ces outils font le mieux — et ce qui fait gagner le plus d'appels."},
            {"type": "h3", "text": "Ce qu'on ne confie pas"},
            {"type": "p", "text": "Les données nominatives d'un client, les pièces d'identité, les coordonnées bancaires : rien de tout cela n'a sa place dans un outil grand public. La règle se pose une fois, par écrit, et tout le cabinet s'y tient."},
        ],
    },
    {
        "slug": "avant-de-creer-sa-societe",
        "title": "Créer sa société : les décisions à prendre avant les papiers",
        "excerpt": (
            "L'immatriculation n'est pas le début du parcours. Quatre décisions "
            "la précèdent, et ce sont elles qui coûtent cher si on les repousse."
        ),
        "category": "Création d'entreprise",
        "date": "9 juillet 2026",
        "date_iso": "2026-07-09",
        "read_time": "6 min",
        "image": "blog-projet.jpg",
        "image_alt": "Ordinateur portable et plans posés sur un bureau",
        "body": [
            {"type": "p", "text": "On aborde souvent la création d'entreprise par les formulaires. Dans les faits, les dossiers qui traînent ne traînent presque jamais pour des raisons administratives : ils traînent parce que des décisions n'ont pas été prises."},
            {"type": "h3", "text": "Qui détient quoi"},
            {"type": "p", "text": "La répartition entre associés se décide avant la rédaction des statuts, pas pendant. Une répartition posée à la va-vite se paie deux ans plus tard, au moment où l'un des associés veut partir."},
            {"type": "h3", "text": "Qui signe"},
            {"type": "p", "text": "Qui engage la société au quotidien, à partir de quel montant, et qui doit contresigner. Écrire ces règles dès le départ évite la moitié des désaccords qui viennent ensuite."},
            {"type": "quote", "text": "Les statuts ne servent pas quand tout va bien. Ils servent le jour où plus personne n'est d'accord."},
            {"type": "h3", "text": "Ce que fait l'entreprise, précisément"},
            {"type": "p", "text": "L'objet social se réfléchit pour couvrir ce que vous ferez dans deux ans, pas seulement ce que vous vendez le premier mois. L'élargir plus tard est possible, mais c'est une formalité de plus."},
            {"type": "h3", "text": "Où elle est domiciliée"},
            {"type": "p", "text": "L'adresse du siège conditionne des démarches et des rattachements. C'est une décision de départ, pas un détail à régler au guichet."},
            {"type": "p", "text": "Ces quatre points réglés, la partie administrative devient un enchaînement de formalités — celui que nous prenons en charge."},
        ],
    },
]

FAQ = [
    {
        "q": "En combien de temps un site est-il en ligne ?",
        "a": "Pour un site vitrine, comptez une à deux semaines une fois les textes "
             "et les photos réunis. C'est presque toujours la collecte des contenus "
             "qui fixe le délai, pas la technique.",
    },
    {
        "q": "Combien ça coûte ?",
        "a": "Le prix dépend de l'ampleur du projet. Après un premier échange gratuit, "
             "vous recevez une proposition écrite avec le détail de ce qui est inclus, "
             "le délai et le montant. Rien ne démarre avant votre accord.",
    },
    {
        "q": "Vous intervenez uniquement à Rabat ?",
        "a": "Nous sommes installés à Rabat et nous nous déplaçons volontiers dans "
             "la région. Le reste du Maroc est couvert à distance, avec des points "
             "réguliers en visioconférence.",
    },
    {
        "q": "Je n'y connais rien en informatique, est-ce un problème ?",
        "a": "Non. C'est même le cas de la plupart de nos clients. Vous décrivez "
             "votre activité, nous traduisons cela en site, en supports et en outils, "
             "puis nous vous formons à ce que vous devrez faire vous-même.",
    },
    {
        "q": "J'ai déjà un site, pouvez-vous le reprendre ?",
        "a": "Oui. Nous regardons d'abord s'il vaut mieux le corriger ou le refaire, "
             "et nous vous disons franchement lequel des deux vous coûtera le moins cher.",
    },
    {
        "q": "Que couvre exactement « création d'entreprise de A à Z » ?",
        "a": "Le choix de la forme juridique, la rédaction et le dépôt des statuts, "
             "l'immatriculation et les démarches administratives et fiscales qui suivent. "
             "Vous signez, nous nous occupons du parcours.",
    },
]

# Contacts directs : aucun compte social n'est inventé, seuls les canaux réels
# que vous nous avez donnés figurent ici.
CONTACTS = [
    {"icon": "message-circle", "label": "WhatsApp", "value": "06 56 18 54 14", "href": SITE["whatsapp"]},
    {"icon": "phone", "label": "Téléphone", "value": SITE["phone_display"], "href": f"tel:{SITE['phone_link']}"},
    {"icon": "mail", "label": "Email", "value": SITE["email"], "href": f"mailto:{SITE['email']}"},
    {"icon": "map-pin", "label": "Adresse", "value": f"{SITE['address']}, {SITE['city']}", "href": None},
    {"icon": "clock", "label": "Horaires", "value": SITE["hours"], "href": None},
]

META_DEFAUT = {
    "titre": f"{SITE['name']} — {SITE['baseline']}",
    "description": (
        "Hushlab accompagne les entreprises à Rabat : création de sites web, QR codes "
        "et NFC pour vos avis et menus, gestion des réseaux sociaux, intelligence "
        "artificielle et création d'entreprise de A à Z."
    ),
    "image": "img/og.jpg",
    "type": "website",
}

SECTIONS = {
    "services": {
        "kicker": "Services",
        "title": "Six métiers, un seul interlocuteur",
        "subtitle": "Vous n'avez plus à coordonner un développeur, une agence de communication, "
                    "un formateur et un juriste. Tout passe par le même contact.",
    },
    "methode": {
        "kicker": "Méthode",
        "title": "Comment on travaille",
        "subtitle": "Quatre étapes, toujours les mêmes, quel que soit le projet.",
    },
    "offres": {
        "kicker": "Offres",
        "title": "Trois façons de démarrer",
        "subtitle": "Chaque projet est chiffré après un échange. Ces formules servent de point de départ.",
    },
    "temoignages": {
        "kicker": "Témoignages",
        "title": "Ce que nos clients en disent",
        "subtitle": None,
    },
    "blog": {
        "kicker": "Blog",
        "title": "Ce qu'on apprend en chemin",
        "subtitle": "Ce qu'on explique le plus souvent à nos clients, écrit une bonne fois.",
        "cta": "Voir tous les articles",
    },
    "faq": {"kicker": "FAQ", "title": "Les questions qu'on nous pose"},
    "contact": {
        "kicker": "Contact",
        "title_plain": "Parlons de votre",
        "title_gradient": "projet",
        "subtitle": "Décrivez votre besoin en quelques lignes, ou appelez directement. "
                    "Le premier échange est gratuit et sans engagement.",
    },
    "cta": {
        "title": "Un projet en tête ? Le premier échange est gratuit",
        "subtitle": "Dites-nous où vous en êtes. Vous repartez avec un avis franc et, si le "
                    "projet tient la route, une proposition écrite.",
        "primary": "Écrire à Hushlab",
        "secondary": "Voir les offres",
    },
}

FOOTER_COLUMNS = [
    {
        "title": "Services",
        "links": [
            {"label": "Création de sites web", "endpoint": "accueil", "anchor": "services"},
            {"label": "QR codes et NFC", "endpoint": "accueil", "anchor": "services"},
            {"label": "Réseaux sociaux", "endpoint": "accueil", "anchor": "services"},
            {"label": "Création d'entreprise", "endpoint": "accueil", "anchor": "services"},
        ],
    },
    {
        "title": "Hushlab",
        "links": [
            {"label": "Méthode", "endpoint": "accueil", "anchor": "methode"},
            {"label": "Offres", "endpoint": "accueil", "anchor": "offres"},
            {"label": "Blog", "endpoint": "blog"},
            {"label": "Contact", "endpoint": "accueil", "anchor": "contact"},
        ],
    },
    {
        "title": "Nous joindre",
        "links": [
            {"label": SITE["phone_display"], "href": f"tel:{SITE['phone_link']}"},
            {"label": "WhatsApp", "href": SITE["whatsapp"]},
            {"label": SITE["email"], "href": f"mailto:{SITE['email']}"},
            {"label": SITE["address"]},
        ],
    },
]

# QR codes suivis : chaque code a une destination et un compteur de scans.
# C'est exactement le produit vendu aux clients (avis, menus, cartes NFC) —
# le site s'en sert d'abord pour lui-même.
QR_CODES = [
    {
        "code": "avis-google",
        "libelle": "Avis Google",
        "cible": "https://www.google.com/search?q=Hushlab+Rabat",
        "aide": "À coller sur le comptoir ou l'addition.",
    },
    {
        "code": "whatsapp",
        "libelle": "WhatsApp",
        "cible": SITE["whatsapp"],
        "aide": "Sur une carte de visite ou une vitrine.",
    },
    {
        "code": "site",
        "libelle": "Site web",
        "cible": "/",
        "aide": "Sur les supports imprimés et les flyers.",
    },
]

SOCIALS = [
    {"label": "WhatsApp", "icon": "message-circle", "href": SITE["whatsapp"]},
    {"label": "Téléphone", "icon": "phone", "href": f"tel:{SITE['phone_link']}"},
    {"label": "Email", "icon": "mail", "href": f"mailto:{SITE['email']}"},
]
