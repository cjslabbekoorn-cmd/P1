"""Haalt de actuele inhoud van live (www.stichtingsampark.nl) en staging op en schrijft content/live.json.

Draaien:  python3 content/build-live.py
Daarna:   docker compose run --rm wpcli eval-file /scripts/content-import.php

Alleen de inhoud wordt opgehaald (tekst, beelden, documenten). Opmaak en pagina-indeling blijven in Elementor.
"""
import html
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

LIVE = "https://www.stichtingsampark.nl"
OUT = Path(__file__).parent / "live.json"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Positie1 Sampark-migratie"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


class Clean(HTMLParser):
    """Houdt alleen inhoud over: tekst, koppen, lijsten, links, beelden en video's. Geen Elementor-wrappers of inline stijl."""
    KEEP = {"p", "h2", "h3", "h4", "strong", "b", "em", "i", "u", "a", "ul", "ol", "li", "blockquote", "br", "img"}
    MAP = {"b": "strong", "i": "em", "h1": "h2", "h5": "h4", "h6": "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.images = [], 0, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "iframe" and "youtube.com/embed/" in a.get("src", ""):
            vid = a["src"].split("/embed/")[1].split("?")[0]
            self.out.append(f"<p>https://www.youtube.com/watch?v={vid}</p>")
            return
        tag = self.MAP.get(tag, tag)
        if tag not in self.KEEP:
            return
        if tag == "img":
            src = a.get("data-src") or a.get("src", "")
            if src.startswith("http") and "/wp-content/uploads/" in src:
                self.images.append(src)
                alt = html.escape(a.get("alt", ""), quote=True)
                self.out.append(f'<img src="{{{{live:{src}}}}}" alt="{alt}">')
            return
        if tag == "a":
            href = a.get("href", "")
            if not href or href.startswith("#"):
                self.out.append("<a>")
                return
            self.out.append(f'<a href="{html.escape(href, quote=True)}">')
            return
        self.out.append(f"<{tag}>" if tag != "br" else "<br>")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.skip -= 1
            return
        tag = self.MAP.get(tag, tag)
        if self.skip or tag not in self.KEEP or tag in ("img", "br"):
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data, quote=False))


def clean(h):
    c = Clean()
    c.feed(h)
    s = "".join(c.out)
    s = re.sub(r"<a>(.*?)</a>", r"\1", s, flags=re.S)               # links zonder doel
    s = re.sub(r" ", " ", s)
    s = re.sub(r"<(p|h2|h3|h4|li|strong|em)>\s*</\1>", "", s)        # lege elementen
    s = re.sub(r"<(p|h2|h3|h4|li|strong|em)>\s*</\1>", "", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    # losse beelden of tekst buiten een alinea: WordPress zet er bij het tonen zelf alinea's omheen (wpautop)
    return s, list(dict.fromkeys(c.images))


def base(url):
    """Bestandsnaam zonder formaat-achtervoegsel (-1024x768) en extensie, om dubbele beelden te herkennen."""
    name = url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return re.sub(r"(-\d+x\d+|-scaled|-e\d+)+$", "", name)


LINKS = [  # oude adressen op live → nieuwe site
    (r"https://www\.stichtingsampark\.nl/sponsors/[^\"]*", "/steun-ons/bedrijven/"),
    (r"https://www\.stichtingsampark\.nl/(?!wp-content/)([^\"]*)", r"/\1"),
]


def tidy(body, title, featured):
    body = re.sub(r"^\s*<p><a href=\"https://www\.stichtingsampark\.nl/\">Home</a></p>", "", body)   # kruimelpad
    m = re.search(r"<h2>(.*?)</h2>", body, flags=re.S)
    if m and text(m.group(1)).lower() == text(title).lower():                                        # titel dubbel
        body = body.replace(m.group(0), "", 1)
    m = re.search(r'<img src="\{\{live:([^}]+)\}\}"[^>]*>', body)
    if m and featured and base(m.group(1)) == base(featured) and body.index(m.group(0)) < 400:         # kopbeeld = uitgelicht beeld
        body = body.replace(m.group(0), "", 1)
    body = body.replace("https://www.sampark.nl/wp-content/", "https://www.stichtingsampark.nl/wp-content/")
    for pat, rep in LINKS:
        body = re.sub(r'href="' + pat + '"', lambda mm: 'href="' + mm.expand(rep) + '"', body)
    # links naar beelden in de uploads: ook importeren
    body = re.sub(r'href="(https://www\.stichtingsampark\.nl/wp-content/uploads/[^"]+\.(?:jpe?g|png|webp))"',
                  r'href="{{live:\1}}"', body)
    body = re.sub(r">\s+<", ">\n<", body)                                                          # witruimte tussen blokken
    body = re.sub(r"\n{2,}", "\n", body).strip()
    # twee of meer beelden achter elkaar worden een fotogrid (CSS .sp-gallery in sampark-styles.php)
    img = r'(?:<a href="[^"]*">)?<img [^>]+>(?:</a>)?'
    def gallery(m):
        items = re.sub(r'(<a href="[^"]*">)?(<img src="\{\{live:([^}]+)\}\}"[^>]*>)(</a>)?',
                       lambda t: t.group(0) if t.group(1) else f'<a href="{{{{live:{t.group(3)}}}}}">{t.group(2)}</a>',
                       m.group(0).strip())
        # alles op één regel: anders zet WordPress (wpautop) <br>'s tussen de foto's
        return '<div class="sp-gallery">' + re.sub(r"\s*\n\s*", "", items) + "</div>\n"
    body = re.sub(rf"(?:{img}\n?){{2,}}", gallery, body)
    body = re.sub(r"<p>\s*(<div class=\"sp-gallery\">.*?</div>)\s*</p>", r"\1", body, flags=re.S)  # geen div in een alinea
    body = re.sub(r"<p>\s*(<div class=\"sp-gallery\">)", r"\1", body)
    return body


def short(t, n=160):
    """Samenvatting voor de nieuwskaart: hooguit n tekens, afgebroken op een woord."""
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0].rstrip(",;:–-") + " …"


def text(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()


# Nieuwscategorie per bericht (slug-deel → categorie); de rest valt onder "Stichting"
CATEGORIES = [
    (("golf", "rally", "autorally", "wijnactie", "netwerk-event", "skutsjesilen", "evenementen"), "evenementen"),
    (("w4y", "meros", "terberg", "canada"), "sponsors-partners"),
    (("school", "holi", "eindsprint", "eindresultaten", "sportdag", "fietsuitreiking", "republiek", "divali",
      "zonnepanelen", "diaries", "godavari", "delhi"), "scholen-leerlingen"),
]
EVENTS = [("golf", "golftoernooi"), ("rally", "sampark-rally"), ("wijnactie", "wijnactie")]
PROJECTS = [("zonnepanelen", ["khukdi-school", "zonnepanelen"]), ("fietsuitreiking", ["fietsen"]),
            ("canada", ["kundanpur-school"]), ("delhi-centre", ["computerspecialist", "modinette", "schoonheidsspecialiste"]),
            ("godavari", ["computerspecialist", "modinette", "schoonheidsspecialiste"])]


def pick(slug, rules, default=None):
    for keys, val in rules:
        if any(k in slug for k in keys):
            return val
    return default


news = []
for p in get(f"{LIVE}/wp-json/wp/v2/posts?per_page=100&_embed=wp:featuredmedia"):
    slug = p["slug"]
    body, _ = clean(p["content"]["rendered"])
    fm = (p.get("_embedded", {}).get("wp:featuredmedia") or [{}])[0].get("source_url")
    body = tidy(body, p["title"]["rendered"], fm)
    images = list(dict.fromkeys(re.findall(r"\{\{live:([^}]+)\}\}", body)))
    news.append({
        "slug": slug, "title": html.unescape(p["title"]["rendered"]), "date": p["date"].replace("T", " "),
        "excerpt": short(text(p["excerpt"]["rendered"]).replace(" [&hellip;]", "").replace(" […]", "")),
        "content": body, "images": images, "featured": fm,
        "cat": pick(slug, CATEGORIES, "stichting"),
        "events": [e for k, e in EVENTS if k in slug],
        "projects": next((v for k, v in PROJECTS if k in slug), []),
        "source": p["link"],
    })

documents = [
    {"key": "algemene_voorwaarden", "title": "Algemene voorwaarden Stichting Sampark",
     "url": f"{LIVE}/wp-content/uploads/2025/03/algemene-voorwaarden-Sampark.pdf"},
    {"key": "jaarrekening_2024", "title": "Jaarrekening 2024 Stichting Sampark", "jaar": "2024", "soort": "Jaarrekening",
     "url": f"{LIVE}/wp-content/uploads/2025/07/Stichting-Sampark-jaarrekening-2024.pdf"},
]

# Evenementen en producten: tijdloze teksten op basis van staging en het wijnbericht van live (sept. 2026).
# Data van de editie 2026 (rally 16 sept., golf 26 okt.) zijn voorbij en bewust weggelaten.
events = {
    "golftoernooi": {
        "content": "<p>Bent u fervent golfer en in het bezit van een golfvaardigheidsbewijs (GVB)? Dan kunt u meedoen aan de wedstrijd en meestrijden om de felbegeerde wisselbeker van het Sampark Golftoernooi.</p>"
                   "<p>Voor deelnemers zonder GVB organiseren we twee clinics: een clinic voor beginners en een masterclass voor gevorderden. De golfers van de masterclass spelen een eigen toernooi op de grote baan.</p>"
                   "<p>U steunt Stichting Sampark met een tafel van € 1.200 voor vier personen, of doet mee voor € 300 per persoon. U krijgt een geheel verzorgde dag, met lunch, diner en een heleboel gezelligheid.</p>"
                   "<p>Het toernooi vindt plaats op de 27-holesbaan van Het Rijk van Nunspeet, Plesmanlaan 30, 8072 PT Nunspeet.</p>",
        "meta": {"locatie_tekst": "Het Rijk van Nunspeet, Plesmanlaan 30, Nunspeet",
                 "programma": [{"tijd": "09:30 – 11:00", "onderdeel": "Ontvangst wedstrijdspelers"},
                               {"tijd": "11:15 – 12:00", "onderdeel": "Ontvangst clinics"},
                               {"tijd": "11:30 – 16:30", "onderdeel": "Wedstrijd (shotgun)"},
                               {"tijd": "12:00 – 16:30", "onderdeel": "Lunch en clinics"},
                               {"tijd": "16:30 – 17:30", "onderdeel": "Aperitief, douchen en omkleden"},
                               {"tijd": "18:00 – 21:00", "onderdeel": "Diner en prijsuitreiking"}]}},
    "sampark-rally": {
        "content": "<p>Een compleet verzorgde dag voor twee personen in een eigen klassieker, met een professioneel uitgezette route en aan het eind een diner waarbij we de winnaars bekendmaken. De opbrengst gaat volledig naar Stichting Sampark.</p>"
                   "<p>Deelname kost € 600 per equipe (twee personen in een eigen auto). Er kunnen maximaal 60 equipes meedoen, dus op = op.</p>"
                   "<p>Meer weten? Neem contact op met Lianne Molhoek via 038 385 50 00 of <a href=\"mailto:info@sampark.nl\">info@sampark.nl</a>.</p>"},
    "wijnactie": {
        "content": "<p>Ieder jaar stellen we vanuit Stichting Sampark een selectie wijnen samen. Dit jaar is er voor het eerst ook een alcoholvrije variant.</p>"
                   "<ul><li><strong>Ruteiro Verdejo 2025:</strong> een frisse, droge Spaanse witte wijn met tonen van perzik, abrikoos en citrus. Heerlijk bij tapas, pasta, gegrilde groenten of als aperitief.</li>"
                   "<li><strong>Palazzo Mio Rosso Negroamaro-Primitivo 2024:</strong> een zachte biologische rode wijn uit Puglia. Soepel en fruitig, lekker bij pasta, pizza, tapas en rood vlees.</li>"
                   "<li><strong>Free Pass White Sparkling Alcoholvrij:</strong> een frisse en fruitige mousserende wijn zonder alcohol, met een fijne bubbel.</li></ul>"
                   "<p>De wijnen worden verkocht per doos van zes flessen voor € 43,95. Laat je bestelling thuisbezorgen of haal hem op afspraak af. Met iedere doos steun je de projecten van Stichting Sampark.</p>",
        "excerpt": "Rood, wit en alcoholvrij. € 43,95 per doos van zes flessen, opbrengst naar de scholen.",
        "thumb": "wijnactie-stichting-sampark-dit-jaar-ook-alcoholvrij",  # uitgelicht beeld van dat nieuwsbericht
        "meta": {"prijs_label": "€ 43,95 per doos"}},
    "project-en-cultuurreis": {
        "content": "<p>Regelmatig organiseert Stichting Sampark een reis naar India. Deelnemers maken kennis met het kleurrijke leven daar en met inspirerende mensen, en zien met eigen ogen het verschil dat hulp kan maken. Een ervaring vol schoonheid, verbondenheid en betekenis.</p>"
                   "<p>Bekijk het avontuur van 2024:</p>\n\nhttps://www.youtube.com/watch?v=a3Bh2of_Nf0\n\n"
                   "<p>Interesse om mee te gaan? Neem contact op via <a href=\"mailto:info@sampark.nl\">info@sampark.nl</a>.</p>"},
}
# Wijnen 2026 zoals op live: eigen namen, prijs € 43,95, eigen productpagina en foto. De slugs van live blijven,
# zodat links naar deze producten na de livegang blijven werken.
live_products = {p["slug"]: p for p in get(f"{LIVE}/wp-json/wc/store/v1/products?per_page=50")}
WINES = {"witte-wijn": "ruteiro-verdejo-2025", "rode-wijn": "palazzo-mio-rosso-negroamaro-primitivo-2024",
         "alcoholvrij": "free-pass-white-sparkling-alcoholvrij"}
products = {}
for old_slug, slug in WINES.items():
    lp = live_products[slug]
    products[old_slug] = {
        "slug": slug, "title": html.unescape(lp["name"]), "price": int(lp["prices"]["price"]) / 100,
        "short": clean(lp["short_description"])[0], "content": clean(lp["description"])[0],
        "image": lp["images"][0]["src"] if lp["images"] else None, "status": "publish"}
products_rest = {
    "golftoernooi": {"content": events["golftoernooi"]["content"]},
    "ticket-sampark-rally": {"content": events["sampark-rally"]["content"]},
}
products.update(products_rest)

OUT.write_text(json.dumps({"news": news, "documents": documents, "events": events, "products": products},
                          ensure_ascii=False, indent=1))
print(f"{len(news)} berichten, {sum(len(n['images']) for n in news)} beelden in tekst, "
      f"{sum(bool(n['featured']) for n in news)} uitgelichte beelden → {OUT}")
