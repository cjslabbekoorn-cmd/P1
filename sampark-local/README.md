# Sampark lokaal (Docker Desktop)

Lokale WordPress-omgeving voor de nieuwe stichtingsampark.nl, volgens `docs/sampark/bouwplan.html` (v2). Het eerste voorstel met de analyse staat in `docs/sampark/structuurvoorstel.html`.

| Dienst      | Adres                         |
|-------------|-------------------------------|
| Site        | http://localhost:8080         |
| Beheer      | http://localhost:8080/wp-admin (admin / admin) |
| phpMyAdmin  | http://localhost:8081         |
| Mailpit     | http://localhost:8025 (alle mail van Woo en Superforms komt hier binnen) |

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

Header en footer zijn lokaal die van Hello Elementor, met wat CSS uit `mu-plugins/sampark-styles.php`. In de echte build worden het Theme Builder-templates (Pro), en die CSS gaat naar Site Settings › Custom CSS.

## Pagina's aanpassen of opnieuw genereren

De pagina-indeling staat als code in `elementor/build.py`. Dat script schrijft per pagina een Elementor-JSON naar `elementor/pages/`. `scripts/build-site.php` zet die in WordPress en vult de beelden in.

```sh
python3 elementor/build.py                                     # JSON opnieuw genereren
docker compose run --rm wpcli eval-file /scripts/build-site.php  # pagina's bijwerken
```

Let op: `build-site.php` overschrijft de Elementor-inhoud van deze pagina's. Wil je een pagina met de hand in Elementor verder bouwen, haal hem dan uit `elementor/pages/` of draai het script niet meer.

Blokken die een JetEngine Listing Grid worden, hebben in de Elementor Navigator een titel die begint met `LISTING ·`, met de query erbij. De kaarten erin zijn het ontwerp van het listing item. De JSON-bestanden zijn ook los te importeren op staging (Elementor › Templates › Importeren); de beeld-placeholders (`{{img:…}}`) zijn dan wel leeg.

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

**Tijdelijk zonder Elementor Pro:** `mu-plugins/sampark-preview-singles.php` toont op `/ons-werk/{school}/` de gebouwde schoolpagina in plaats van de kale projectsingle. Verwijder die mu-plugin zodra er een Theme Builder Single-template voor projecten is.

## Super Forms

Super Forms 6.3 wordt geïnstalleerd, met de meegeleverde add-ons (waaronder WooCommerce). De productformulieren van staging staan er nog niet in. Exporteer ze op staging (Super Forms › Forms › Export) en importeer ze lokaal, of zet het exportbestand in `plugins/premium/`. Dan zet ik ze op de producten.

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

Gebruik je gebruikelijke migratietool (bijvoorbeeld All-in-One WP Migration of WP Migrate). Of exporteer de database en vervang de URL met `wp search-replace http://localhost:8080 https://staging.stichtingsampark.nl`.
