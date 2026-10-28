#!/bin/sh
# Bouwt pagina's, templates en de Elementor-kit opnieuw op uit de generator (elementor/) en zet daarna de inhoud
# van live er weer in. Gebruik dit alleen zolang er nog niets met de hand in Elementor is aangepast:
# handwerk op pagina's en templates wordt overschreven. Berichten, evenementen, producten en formulieren blijven.
#
#   docker compose run --rm wpcli sh /scripts/rebuild.sh
set -eu
wp() { command wp --path=/var/www/html "$@"; }
log() { printf '\n==> %s\n' "$*"; }

log "Back-up van de database"
wp db export "/backups/sampark-voor-rebuild-$(date +%Y%m%d-%H%M).sql" >/dev/null && echo "  in backups/"

log "Super Forms: ontbrekende formulieren"
wp eval-file /scripts/superforms-import.php 2>&1 | grep -v SERVER_NAME || true

log "Winkelinstellingen"
wp eval-file /scripts/shop-settings.php 2>&1 | grep -E "^\s+[+~]|Warning|Error" || true

log "JetEngine: ontbrekende queries en listings"
wp eval-file /scripts/jetengine-setup.php 2>&1 | grep -E "^\s+\+|Warning|Error" || true

log "Pagina's, templates en kit opnieuw opbouwen"
wp eval-file /scripts/build-site.php --exec="define('SP_FORCE', true);" 2>&1 | grep -E "^\s+[+~-]|Warning|Error" || true

log "Inhoud van live opnieuw toepassen (ANBI-documenten, bestaande berichten blijven)"
wp eval-file /scripts/content-import.php 2>&1 | grep -E "nieuws:|ANBI|Warning|Success" || true

wp rewrite flush --hard >/dev/null 2>&1 || true
log "Klaar"
