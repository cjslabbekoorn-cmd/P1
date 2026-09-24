# All You Can Learn

Online leerplatform voor het mbo (keuzedelen en burgerschap), gebruikt door tientallen mbo-scholen.

## Site

- Live: https://allyoucanlearn.nl/ (www stuurt door naar zonder www)
- Platform: WordPress, achter Cloudflare
- Thema: Hello Elementor met child-thema `hello-theme-child-master`
- Belangrijkste plugins (gezien in de HTML, 24-09-2026): Elementor 4.2 + Elementor Pro, JetEngine, JetMenu, JetTabs, JetSmartFilters, Relevanssi Live Ajax Search, WP Rocket
- REST API: `/wp-json/` is bereikbaar

## Aandachtspunten

- De opmaak van pagina's zit grotendeels in Elementor, dus in de database en niet in themabestanden. Eigen code hoort in het child-thema (of een eigen plugin) onder `code/`, niet in het hoofdthema of in plugins van derden.
- WP Rocket en Cloudflare cachen: na een wijziging kan het even duren voor die live zichtbaar is.

## Nog in te vullen

- [ ] Hosting en toegang (FTP/SFTP, beheer-login, REST API-gebruiker)
- [ ] Contactpersoon en afspraken over wat wel/niet aangepast mag worden
- [ ] Eerste opdrachten
