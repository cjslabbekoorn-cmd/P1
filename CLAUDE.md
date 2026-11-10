# Stichting Sampark: nieuwe website

Overdracht voor verdere sessies. Stand van zaken: 10 november 2026.

## Afspraken

- **Alles in het Nederlands**: antwoorden, commits, documentatie en teksten op de site.
- Werkwijze Positie1: Elementor Pro en JetEngine (widgets, listings, queries), WooCommerce, Super Forms voor de
  productformulieren, Code Snippets voor maatwerk-PHP. Stijl komt van de oude staging, inhoud van live.
- Nooit wachtwoorden, licentiesleutels of API-sleutels in de chat of in de repo. De gebruiker vult die zelf in
  wp-admin in (Mollie, Mailchimp, licenties).
- Geen volledige AIOM-exports of databasedumps delen of committen: daar staan persoonsgegevens in. De map
  `sampark-local/backups/` wordt door git genegeerd.
- Werk op branch `claude/busy-shannon-g81gyl`; geen pull request zonder dat erom gevraagd is.
- Commitberichten eindigen met `Co-Authored-By: Claude <noreply@anthropic.com>`.

## Omgevingen

| Omgeving | Adres | Rol nu |
|---|---|---|
| Lokaal (Docker Desktop op de Mac) | http://localhost:8600 (phpMyAdmin 8601, Mailpit 8602) | Bron van de import op staging; nu alleen nog om iets uit te proberen |
| Staging | https://staging.stichtingsampark.nl | **Hier wordt verder gewerkt.** Lokale site is op 9 november 2026 met All-in-One WP Migration geïmporteerd |
| Live | https://www.stichtingsampark.nl | Oude site; wordt in fase 3 vervangen door staging |

**Belangrijk:** staging is nu de plek waar de site verder groeit. Exporteer de lokale site **niet** nog een keer
over staging heen, want dan gaat alles verloren wat op staging is ingesteld of aangepast (licenties, Mollie, plugins,
teksten). Wijzigingen op staging doe je in wp-admin en Elementor.

De scripts in `sampark-local/scripts/` draaien via WP-CLI in Docker en werken alleen lokaal. Op staging is geen
WP-CLI of SSH aangenomen. Moet een script toch op staging draaien, vraag dan eerst of de hoster SSH/WP-CLI biedt,
of zet de logica om naar een Code Snippet die je één keer uitvoert.

## Wat er op de site staat

Volledige beschrijving: `sampark-local/README.md`. In het kort:

- **Posttypes (JetEngine):** projecten (`/ons-werk/`), evenementen, sponsors; Options Page `stichting` met
  bedrijfsgegevens, ANBI en documenten; glossaries Evenementstatus en Wat Sampark betaalt.
- **Relaties:** Evenement → Product, Evenement ↔ Bericht, Project ↔ Bericht, Sponsor ↔ Evenement.
- **Theme Builder-templates:** singles voor project, evenement, bericht en product (varianten wijn, rally, golf,
  donatie met Super Forms), nieuwsarchief.
- **Evenementpagina:** inschrijfsectie gericht op conversie (listing *Inschrijfkaart groot*; bij de wijnactie
  *Bestelkaart* met "Bestel nu"). Of "Schrijf je in" of "Bestel nu" verschijnt, regelt CSS op basis van de
  aanwezige producten.
- **Winkel:** `/winkelwagen/`, `/afrekenen/`, `/mijn-account/` in de opmaak van de oude staging; `/bedankt/`
  (Purchase Summary, stap "op factuur" alleen bij betalen op factuur) en `/betaling-mislukt/` (met "Opnieuw
  betalen"). Betaalmethoden: "Op factuur" (WooCommerce BACS) en "Inbegrepen in mijn sponsorpakket" (cheque).
- **Code Snippets (4, actief):** factuur-opmaak, donatie-prijs, sponsor-betaling (golf/rally op € 0 bij
  sponsorpakket), betaling-mislukt. Broncode in `sampark-local/snippets/`.
- **Extra CSS:** staat in Elementor › Site-instellingen › Aangepaste CSS tussen `/* sampark-styles begin */` en
  `/* sampark-styles einde */`. De bron is `sampark-local/mu-plugins/sampark-styles.css`. Pas de CSS op staging aan
  in Elementor en zet dezelfde wijziging in dat bestand, anders lopen ze uit elkaar.
- **Redirects:** 21 regels in Redirection (bron: `sampark-local/content/redirects.csv`), voor de oude adressen van
  live.

## Waar we gebleven zijn: stap 4 op staging

De import op staging is klaar. Nog af te vinken (de gebruiker doet dit in wp-admin):

- [ ] Permalinks opslaan
- [ ] Eigen beheerder met sterk wachtwoord; gebruiker `admin` verwijderen (inhoud toeschrijven aan de nieuwe beheerder)
- [ ] Licenties: Elementor Pro, JetEngine (Crocoblock), Super Forms
- [ ] Elementor › Tools › CSS en gegevens opnieuw genereren, bibliotheek synchroniseren
- [ ] Controleren: home, een evenement (rally) en de winkelwagen zien er hetzelfde uit als lokaal
- [ ] Installeren en instellen: Mollie Payments (testmodus, iDEAL), PDF Invoices & Packing Slips, WP Rocket,
      Wordfence, Cookiebot
- [ ] GTM4WP: container `GTM-5G2QJQS`
- [ ] Instellingen › Lezen: "Zoekmachines ontmoedigen" blijft aan
- [ ] Verwijderen als ze er nog staan: Woo Discount Rules (+ Pro), Ultimate Dashboard, JetElements,
      JetSmartFilters, Product Add-Ons, Donations for WooCommerce
- [ ] WP Rocket-cache legen
- [ ] Schijfruimte bij de hoster controleren. De oude staging was een export van 3,6 GB, de nieuwe 475 MB. Blijft
      het gebruik hoog, dan staan er nog oude uploads en is opruimen nodig.

## Daarna: stap 5, testen op staging

- [ ] Elke betaalroute: iDEAL (Mollie test), op factuur, inbegrepen in sponsorpakket (golf en rally op € 0)
- [ ] Mislukte en afgebroken iDEAL-betaling: komt de klant op `/betaling-mislukt/` en werkt "Opnieuw betalen"?
      (In Mollie-testmodus kies je de status zelf.)
- [ ] Elk formulier: wijn (bezorgen en afhalen), rally, golf (ook met sponsorpakket), donatie (productpagina en
      `/steun-ons/doneren/`), sponsorpakket
- [ ] Mails: bestelbevestiging, factuur-pdf, formuliermail; afzender en logo
- [ ] Cookiebot blokkeert YouTube en GTM tot er toestemming is
- [ ] Kaart op Ons werk en op de schoolpagina's
- [ ] Mobiel, toetsenbord en contrast
- [ ] Snelheid met WP Rocket aan; geen dubbele of ontbrekende CSS
- [ ] Redirects: bijvoorbeeld `/projecten/khukdi/` → `/ons-werk/khukdi/`

## Nog open (ligt bij de stichting of de gebruiker)

- Privacyverklaring is nog de standaardtekst van WordPress.
- Beleidsplan en verslag van activiteiten voor de ANBI-pagina; eventueel eerdere jaarrekeningen.
- Juiste coördinaten van de scholen in Khukdi en Ghadia.
- Nieuwsbericht "Holi-vreugde en een welverdiende pauze!" heeft geen uitgelichte afbeelding.
- Mailchimp for WooCommerce koppelen en het nieuwsbriefformulier in de footer aan de juiste lijst hangen.
- BTW-nummer: moet het op de site of de factuur?
- Oude bestellingen en klantaccounts van live: archiveren (A, aanbevolen) of overzetten (B)? Graag met aantallen.
- Datum van de livegang: een rustige avond, buiten een lopende inschrijving.

## Fase 3: livegang

Het draaiboek staat in het migratieplan (Claude-document):
https://claude.ai/artifact/CFRLcQUSU9o4GSmk12Mpvb

In het kort: live in onderhoudsmodus, AIOM-back-up van live, bestellingen exporteren, nieuwe nieuwsberichten
van live meenemen, staging exporteren en importeren op live, Mollie naar live-modus, zoekmachines toestaan,
redirects controleren, testdonatie van € 5 met iDEAL en terugbetalen, sitemap indienen in Search Console. Vóór de
export van staging: testbestellingen, testklanten en formulierinzendingen van staging verwijderen.

## Lokaal nog iets proberen

```bash
cd ~/P1/sampark-local
docker compose up -d                                         # site op http://localhost:8600
docker compose run --rm wpcli eval-file /scripts/staging-klaar.php   # controles
```

Inlog lokaal: zie `WP_ADMIN_USER` en `WP_ADMIN_PASSWORD` in `sampark-local/.env`. Wat lokaal werkt, zet je op
staging met de hand over in Elementor of wp-admin, niet met een nieuwe export.
