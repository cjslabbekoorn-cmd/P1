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
   - `elementor-pro` (4.1.x, gelijk aan staging; 3.x past niet op Elementor 4)
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

## Handmatig in JetEngine

Positie1 richt dit altijd via de JetEngine-interface in, zodat het exporteerbaar en overdraagbaar blijft. Zet bij elk datumveld **Save as timestamp** aan.

**Post Types**
- `evenementen` (archief uit, slug `evenementen`; de pagina /evenementen/ is het overzicht): status (select: aangekondigd / open / vol / doorlopend / afgelopen), datum_start, datum_eind, tijd, locatie, inschrijving_tot, prijs_label, max_deelnemers, externe_inschrijflink, programma (repeater: tijd + onderdeel), galerij.
- `projecten` (archief uit, rewrite-slug `ons-werk`; de pagina /ons-werk/ is het overzicht): tagline, aantal, eenheid (leerlingen / studenten), soort_werk (nieuwbouw / renovatie / doorlopend), sinds, we_financieren (checkbox), externe_link, galerij.
- `sponsors` (*publicly queryable* uit): logo, website, actief (switcher), volgorde.

**Taxonomies**
- `projecttype` op projecten: School, Opleiding, Initiatief.
- `regio` op projecten: Budaun, New Delhi.
- `sponsorniveau` op sponsors: Sona, Chandee, Peetal, Partner.

**Relations**
- Evenement → Product (one to many)
- Evenement ↔ Bericht (many to many)
- Project ↔ Bericht (many to many)
- Sponsor ↔ Evenement (many to many)

**Options Page "Stichting"**: kerncijfers, contact (adres, telefoon, e-mail, bereikbaarheid), registratie (KvK, RSIN, IBAN), campagne (switcher, tekst, link), bestuur (repeater), tijdlijn (repeater), anbi_documenten (repeater), anbi_teksten.

Exporteer de JetEngine-configuratie na het inrichten (JetEngine → Dashboard → Import/Export) en zet het JSON-bestand in `jetengine/`. Dan kan een volgende ontwikkelaar het in één keer importeren.

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
