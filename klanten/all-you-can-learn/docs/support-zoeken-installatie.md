# AYCL Support Zoeken: installatie

Vervangt Relevanssi en de bijbehorende snippet voor de zoekfunctie op /kennisbank/ (CPT `support`).

## Stappen

1. **Snippet uitzetten.** De oude Relevanssi-snippet roept functies aan die zonder Relevanssi niet bestaan. Die moet uit, anders geeft de live-zoekfunctie een fatale fout.
2. **Relevanssi uit laten** (is al gedeactiveerd).
3. **Plugin installeren:** wp-admin → Plugins → Nieuwe plugin → Plugin uploaden → `aycl-support-zoeken.zip` → Activeren.
4. **Controleren** op /kennisbank/:
   - live-resultaten tijdens het typen (vanaf 3 tekens);
   - de resultatenpagina na Enter;
   - de filters (JetSmartFilters) op de rest van de site.
5. **Cache legen** in WP Rocket, en zo nodig in Cloudflare.

In Elementor hoeft niets te veranderen: de zoekwidget houdt Query ID `relevanssi_search`.

## Terugdraaien

Deactiveer de plugin in wp-admin. Lukt dat niet, hernoem dan via FTP de map `wp-content/plugins/aycl-support-zoeken`.

## Relevanssi Live Ajax Search

De Elementor-zoekwidget heeft zelf live-resultaten (template 17393). `relevanssi-live-ajax-search` is daarvoor niet nodig. Die plugin haakt in op alle zoekvelden van de site en zoekt dan in alle berichttypes. Advies: ook uitzetten, en controleren of de zoekfunctie ergens anders op de site hem nodig heeft.

## Vergelijking met Relevanssi op staging (24-09-2026)

Alle 130 kennisbank-artikelen van staging zijn in een test-WordPress gezet. Daarna zijn 16 zoekopdrachten vergeleken met de live-resultaten van de widget op staging, waar Relevanssi nog actief was.

- **Welke artikelen er gevonden worden:** bij elke zoekopdracht dezelfde als Relevanssi.
- **Volgorde:** in de top 10 grotendeels gelijk, met 116 van de 138 artikelen overlap. De exacte plek verschilt soms. Een nagebouwde Relevanssi-formule kwam niet dichterbij.
- **Verschil:** Relevanssi vulde de lijst op staging na de echte treffers aan met artikelen waarin het zoekwoord niet voorkomt. Bij "cookies" kwamen er na 6 treffers bijvoorbeeld "betaalmethodes" en "toegankelijkheid". Die bevatten "cookies" alleen in footer en metadata. De plugin toont alleen echte treffers.

## Hoe de relevantie werkt

- Eén zoekwoord volstaat (OF), net als bij Relevanssi op deze site. Artikelen met meer zoekwoorden scoren hoger. Met de filter `aycl_zoek_operator` (waarde `en`) moeten eerst alle woorden voorkomen.
- Gewicht per treffer:
  - titel 5, samenvatting 2, inhoud 1;
  - een heel woord telt zwaarder dan een deel van een woord ("inlog" vindt ook "inloggen");
  - de hele zoekzin in de titel geeft een bonus.
- Hoofdletters en accenten maken niet uit.
- Bij gelijke score komt het nieuwste artikel eerst.
- Gewichten aanpassen kan met de filter `aycl_zoek_gewichten`.
