# Sampark lokaal (Docker Desktop)

Lokale WordPress-omgeving voor de nieuwe stichtingsampark.nl, volgens `docs/sampark/bouwplan.html` (v2). Het eerste voorstel met de analyse staat in `docs/sampark/structuurvoorstel.html`.

| Dienst      | Adres                         |
|-------------|-------------------------------|
| Site        | http://localhost:8600         |
| Beheer      | http://localhost:8600/wp-admin (admin / admin) |
| phpMyAdmin  | http://localhost:8601         |
| Mailpit     | http://localhost:8602 (alle mail van Woo en Superforms komt hier binnen) |

## Eerste keer

1. Installeer en start **Docker Desktop**.
2. Zet de premium plugins in `plugins/premium/`, als zip of als map (bijvoorbeeld via FTP gedownload uit `wp-content/plugins/` van staging):
   - `elementor-pro` (4.1.x, gelijk aan staging; 3.x past niet op Elementor 4) — nog nodig voor header, footer en de single-templates
   - `jet-engine`, `jet-elements`, `jet-smart-filters`
   - `super-forms` plus de Super Forms-add-ons voor WooCommerce
   Deze bestanden staan niet in git (licenties). Elementor zelf wordt op 4.1.5 gezet, de versie van staging.
   Fonts: Aptos komt uit Adobe Fonts-project `nnd7fbm` (instelbaar met `ADOBE_FONTS_PROJECT` in `.env`).
3. Open een terminal in deze map (`sampark-local/`) en draai:

   ```sh
   cp .env.example .env
   docker compose up -d
   docker compose run --rm wpcli sh /scripts/setup.sh
   ```

   Op Windows werkt dit ook in PowerShell; gebruik `copy` in plaats van `cp`.

4. Activeer de licenties van Elementor Pro, JetEngine en Super Forms in wp-admin.

Het setupscript kun je altijd opnieuw draaien, bijvoorbeeld nadat je zips hebt toegevoegd. Wat al bestaat wordt overgeslagen.

### Wat het script neerzet

- WordPress in het Nederlands, permalinks `/%postname%/`, tijdzone Amsterdam, niet indexeerbaar.
- Thema Hello Elementor, plus WooCommerce, Elementor, Yoast SEO en Redirection. De zips uit `plugins/premium/` worden geïnstalleerd.
- De huisstijl als Elementor-kit, 1-op-1 van staging: kleuren, Spectral / Patrick Hand / Aptos, knoppen, formuliervelden, afbeeldingsradius en containerbreedte. Oude kleuren van de vorige site zijn weggelaten.
- Ongeveer 50 beelden van staging (hero's, scholen, opleidingen, bestuur, sponsorlogo's) en de getekende iconen uit `assets/icons/`.
- De pagina's uit het bouwplan (`docs/sampark/bouwplan.html`), gebouwd met Elementor-containers: Home, Ons werk, Evenementen, Steun ons met Doneren en Voor bedrijven, Over ons met ANBI & financiën, en Contact. Plus Nieuws (berichtenpagina), de juridische pagina's en de Woo-pagina's (`/winkelwagen/`, `/afrekenen/`, `/mijn-account/`, `/shop/`).
- Nieuwscategorieën: Scholen & leerlingen, Evenementen, Sponsors & partners, Stichting (standaard).
- Productcategorieën en de 10 producten met prijzen. "Alcoholvrij mousserend" staat als concept, omdat de prijs nog ingevuld moet worden.
- Menu's: Hoofdmenu (met submenu's onder Steun ons en Over ons), Topbalk, Footer – Direct naar, Footer – Juridisch.

**Header en footer** zijn Theme Builder-templates (Elementor Pro), gemaakt door `build-site.php` vanuit `elementor/templates/`:
- Header: topbalk (Voor bedrijven, Contact, Mijn account; verborgen op mobiel) en een sticky hoofdbalk met logo, hoofdmenu met uitklapmenu's, Doneer-knop en winkelmandje. Op mobiel staan logo, Doneer, winkelmandje en de menuknop op één regel.
- Footer: logo, tagline en social media, contactgegevens en KvK/RSIN/IBAN live uit de Options Page "Stichting" (JetEngine), het menu "Direct naar", een nieuwsbriefformulier (Elementor Form; nu met e-mail naar info@, Mailchimp na keuze), het juridische menu en het ANBI-logo.

Zonder Elementor Pro valt de site terug op de header en footer van Hello Elementor (met wat CSS uit `mu-plugins/sampark-styles.php`). Die CSS hoort in productie in Site Settings › Custom CSS.

## Pagina's aanpassen of opnieuw genereren

De pagina-indeling staat als code in `elementor/build.py`. Dat script schrijft per pagina een Elementor-JSON naar `elementor/pages/`. `scripts/build-site.php` zet die in WordPress en vult de beelden in.

```sh
python3 elementor/build.py                                     # JSON opnieuw genereren
docker compose run --rm wpcli eval-file /scripts/build-site.php  # pagina's bijwerken
```

Let op: `build-site.php` overschrijft de Elementor-inhoud van deze pagina's. Wil je een pagina met de hand in Elementor verder bouwen, haal hem dan uit `elementor/pages/` of draai het script niet meer.

Blokken die een JetEngine Listing Grid worden, hebben in de Elementor Navigator een titel die begint met `LISTING ·`, met de query erbij. De kaarten erin zijn het ontwerp van het listing item. De JSON-bestanden zijn ook los te importeren op staging (Elementor › Templates › Importeren); de beeld-placeholders (`{{img:…}}`) zijn dan wel leeg.

## Plugins

Afgesproken set (27-10-2026). Het setupscript installeert alles behalve de live-only plugins.

| Plugin | Status | Opmerking |
|---|---|---|
| Elementor + Elementor Pro 4.1.3 | blijft | Pro uit `plugins/premium/` |
| JetEngine 3.8.10 | blijft | uit `plugins/premium/` |
| Super Forms 6.3 | blijft | alleen de WooCommerce-add-on in gebruik |
| WooCommerce | blijft | |
| Yoast SEO, Redirection | blijft | |
| Mailchimp for WooCommerce | blijft | koppelen via de wizard met het Mailchimp-account (niet lokaal) |
| GTM4WP | blijft | container `GTM-5G2QJQS`; lokaal uit, zet `GTM_ID` in `.env` om te testen |
| Code Snippets | blijft | de 3 Sampark-snippets uit `snippets/` (zie hieronder) |
| PDF Invoices & Packing Slips | blijft | nodig voor het snippet "factuur en pakbon"; niet lokaal |
| Mollie, WP Rocket, Wordfence, Cookiebot | alleen staging/live | niet lokaal |
| Woo Discount Rules (+ Pro) | gaat eruit | vervangen door het snippet "deelname via sponsorpakket" |
| Ultimate Dashboard | gaat eruit | |
| Invoice Gateway for WooCommerce | gaat eruit | "Op factuur" is de standaard WooCommerce-betaalmethode Bankoverschrijving, hernoemd |
| JetElements, JetSmartFilters, Product Add-Ons, Donations for WooCommerce | gaat eruit | niet gebruikt in de nieuwe opzet |
| WP All Import, All-in-One WP Migration, Jetpack | na de migratie weg | |

## JetEngine (automatisch)

Staat JetEngine in `plugins/premium/`, dan richt `scripts/jetengine-setup.php` het in via de eigen tools van JetEngine (de MCP-features `add-cpt`, `add-taxonomy`, `add-glossary`, `add-query`, `manage-modules`) en de dataklassen voor relaties, de Options Page en listings. Alles staat daarna gewoon in de JetEngine-interface.

- **Modules:** Maps Listings, Dynamic Visibility, Grid- en Slider-galerij aan; de rest uit.
- **Kaart:** provider Leaflet, geocoding OpenStreetMap (geen API-sleutel).
- **Posttypes:**
  - `projecten` (URL `/ons-werk/…`, geen archief): tagline, aantal, eenheid, soort werk, dorp, **locatie (Map-veld)**, feiten (repeater), tweede kop + tekst, voorzieningen, wat Sampark betaalt (checkbox), momenten (repeater), externe link, galerij.
  - `evenementen` (URL `/evenementen/…`, geen archief): status, datum, einddatum, datumtekst, inschrijven tot, tijd, locatie, prijs, max. deelnemers, externe inschrijflink, programma (repeater), galerij. Sortering op volgorde (Pagina-attributen), zodat evenementen zonder vaste datum niet wegvallen.
  - `sponsors` (niet publiek): website, tonen aan/uit.
- **Taxonomieën:** `projecttype` (scholen / opleidingen / initiatieven), `regio`, `sponsorniveau`.
- **Glossary:** Evenementstatus (aangekondigd, inschrijving open, vol, het hele jaar, afgelopen).
- **Options Page "Stichting":** kerncijfers, contact en registratie, campagnebadge, bestuur en tijdlijn, ANBI-teksten en -documenten.
- **Relaties:** Evenement → Product, Evenement ↔ Bericht, Project ↔ Bericht, Sponsor ↔ Evenement.
- **11 queries** (Query Builder) en **6 listings**: projectkaart, evenementkaart, sponsorlogo, nieuwskaart, sponsorpakket en de kaart-popup.
- **Inhoud:** de 4 scholen, 3 opleidingen en 4 initiatieven met alle velden en coördinaten, 5 evenementen, 10 sponsors, 4 nieuwsberichten en de Options Page. Bestaande inhoud wordt nooit overschreven.

Daarna bouwt `build-site.php` de pagina's opnieuw. De `LISTING ·`-blokken worden echte **JetEngine Listing Grids** en de kaart wordt een **JetEngine Map Listing** met clustering en popup.

**Naar staging:** `docker compose run --rm wpcli eval-file /scripts/jetengine-export.php` schrijft `jetengine/sampark-jetengine.json`. Importeer dat op staging via JetEngine › Dashboard › Skins › Import. Let op: staging heeft al posttypes `projecten` en `evenementen` met eigen velden. Kies bij de import per item "vervangen" of "overslaan", en vergelijk eerst de veldnamen, zodat er geen bestaande data verloren gaat. Listing Grids op pagina's moeten na import opnieuw naar de juiste listing en query wijzen, omdat de ID's op staging anders zijn.

## Single-templates (Elementor Pro Theme Builder)

Detailpagina's zijn geen losse pagina's meer, maar één template per type. De inhoud komt uit de velden van het bericht, dus een nieuwe school of een nieuw evenement aanmaken in JetEngine is genoeg.

| Template | Voorwaarde | Inhoud |
|---|---|---|
| Single · Project | alle projecten (`/ons-werk/…`) | hero met uitgelichte afbeelding, feiten, verhaal en voorzieningen, wat Sampark betaalt (checklist met glossary), tijdlijn, kaart met dit project, galerij, gekoppeld nieuws, andere projecten van hetzelfde type |
| Single · Evenement | alle evenementen | status, praktische info (datum, tijd, locatie, kosten, inschrijven tot, deelnemers), beschrijving en programma, inschrijfkaarten van de gekoppelde producten of de externe inschrijflink, galerij, sponsors, terugblikken |
| Single · Nieuwsbericht | alle berichten | datum, titel, intro, beeld, tekst, gekoppelde projecten en evenementen, meer nieuws |
| Product · winkelwagenknop | alle producten | beeld, titel, prijs, korte omschrijving, bestelknop (sponsorpakketten, sponsor een kind) |
| Product · wijnactie / Sampark Rally / golftoernooi / donatie | productcategorie | idem, maar met het Super Forms-formulier in plaats van de bestelknop |

- Secties met een optioneel veld (feiten, tijdlijn, kaart, galerij, programma …) hebben **Dynamic Visibility** "veld bestaat" en verdwijnen als het veld leeg is.
- Secties met een gekoppelde lijst (nieuws, sponsors, inschrijven …) hebben een Listing Grid met "Hide widget if: Query is empty" en de CSS-klasse `sp-hide-empty`, zodat ook de kop verdwijnt.
- De queries hiervoor (`Single · …` in de Query Builder) gebruiken de JetEngine-macro's `%current_id%`, `%current_terms|projecttype%` en `%rel_get_items|…%`.
- Koppel een product aan een evenement via de relatie **Evenement → Product**; het verschijnt dan als inschrijfkaart op het evenement.

De oude losse schoolpagina's onder `/ons-werk/` gaan bij `build-site.php` naar de prullenbak.

## Super Forms

Super Forms 6.3 wordt geïnstalleerd, met de meegeleverde add-ons (waaronder WooCommerce). `scripts/superforms-import.php` zet de 4 formulieren van staging neer uit `superforms/forms.json`: Wijn, Rally, Golftoernooi en Donatie (zonder de 100 back-ups en zonder opgeslagen geheimen).

## Snippets (Code Snippets)

`scripts/snippets-import.php` zet de snippets uit `snippets/` in Code Snippets en zet ze aan. Bestaande snippets met dezelfde naam worden bijgewerkt. Draai het met `--exec="define('CODE_SNIPPETS_SAFE_MODE', true);"` (zoals `setup.sh` doet), anders weigert Code Snippets het (opnieuw) activeren.

| Snippet | Bron | Wat het doet |
|---|---|---|
| Factuur en pakbon: regelgegevens | staging, ongewijzigd | extra regelgegevens op factuur/pakbon (PDF Invoices & Packing Slips) |
| Donatiebedrag als prijs | staging, ID 4040 vervangen door slug `donatie` | het bedrag uit het donatieformulier wordt de prijs van de regel |
| Deelname via sponsorpakket | nieuw, vervangt Woo Discount Rules | golftoernooi en rally-ticket € 0 bij betaalmethode "Inbegrepen in mijn sponsorpakket" (`cheque`) |

Uit Woo Discount Rules was alleen regel "Sponsorpakket" actief (100% korting op golf bij betaalmethode cheque). De uitgeschakelde "Wijnactie" (6+1 gratis) en de 3 voorbeeldregels zijn niet overgenomen. Het snippet "Sponsorpakketten – icoonweergave" vervalt, omdat de organische vormen niet meer gebruikt worden.

Het sponsorsnippet werkt met de klassieke afrekenpagina (shortcode `[woocommerce_checkout]`), die het setupscript instelt; de blok-checkout herberekent niet bij wisselen van betaalmethode.

## Dagelijks gebruik

```sh
docker compose up -d                       # starten
docker compose stop                        # stoppen (data blijft bewaard)
docker compose run --rm wpcli plugin list  # elk wp-cli-commando
docker compose run --rm wpcli db export /backups/sampark-$(date +%F).sql
docker compose run --rm wpcli db import /backups/<bestand>.sql
docker compose down -v                     # alles weggooien, inclusief database
```

## Naar staging of live

Gebruik je gebruikelijke migratietool (bijvoorbeeld All-in-One WP Migration of WP Migrate). Of exporteer de database en vervang de URL met `wp search-replace http://localhost:8600 https://staging.stichtingsampark.nl`.
