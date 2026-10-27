# Sampark lokaal (Docker Desktop)

Lokale WordPress-omgeving om de nieuwe structuur van stichtingsampark.nl op te bouwen, volgens `docs/sampark/structuurvoorstel.html`.

| Dienst      | Adres                         |
|-------------|-------------------------------|
| Site        | http://localhost:8080         |
| Beheer      | http://localhost:8080/wp-admin (admin / admin) |
| phpMyAdmin  | http://localhost:8081         |
| Mailpit     | http://localhost:8025 (alle mail van Woo en Superforms komt hier binnen) |

## Eerste keer

1. Installeer en start **Docker Desktop**.
2. Zet de premium plugins als zip in `plugins/premium/`:
   - `elementor-pro.zip`
   - `jet-engine.zip`
   - `super-forms.zip` plus de Super Forms add-on voor WooCommerce die op staging gebruikt wordt
   Deze zips staan niet in git (licenties).
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
- Pagina's: Home (voorpagina), Nieuws (berichtenpagina), Steun ons, Sponsors, Over ons met ANBI & financiën, Contact, Algemene voorwaarden, Privacyverklaring, Sitemap, en de Woo-pagina's (`/shop/`, `/winkelwagen/`, `/afrekenen/`, `/mijn-account/`).
- Nieuwscategorieën: Scholen & leerlingen, Evenementen, Sponsors & partners, Stichting (standaard).
- Productcategorieën en de 10 producten met prijzen. "Alcoholvrij mousserend" staat als concept, omdat de prijs nog ingevuld moet worden.
- Menu's: Hoofdmenu, Footer – Direct naar, Footer – Juridisch. Wijs ze toe in het Elementor Nav Menu-widget van de header/footer.

`/projecten/` en `/evenementen/` bestaan nog niet; die maakt JetEngine aan als CPT-archief (zie hieronder).

## Handmatig in JetEngine

Positie1 richt dit altijd via de JetEngine-interface in, zodat het exporteerbaar en overdraagbaar blijft. Zet bij elk datumveld **Save as timestamp** aan.

**Post Types**
- `evenementen` (archief aan, slug `evenementen`): status (select: aangekondigd / open / vol / doorlopend / afgelopen), datum_start, datum_eind, tijd, locatie, inschrijving_tot, prijs_label, max_deelnemers, programma (repeater: tijd + onderdeel), galerij.
- `projecten` (archief aan, slug `projecten`): tagline, aantal, soort_werk (nieuwbouw / renovatie / doorlopend), sinds, we_financieren (checkbox), externe_link, galerij.
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
