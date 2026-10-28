<?php
/**
 * Voegt pagina's (elementor/pages/) en Theme Builder-templates (elementor/templates/) toe die nog niet in de site staan.
 * Bestaande pagina's, templates en de Elementor-kit blijven ongemoeid, dus veilig op een site die met de hand
 * in Elementor verder wordt gebouwd.
 *
 *   docker compose run --rm wpcli eval-file /scripts/templates-add.php
 *
 * Zet ook de markering "met de hand verder gebouwd", zodat build-site.php niet per ongeluk alles overschrijft.
 */

define( 'SP_ALLEEN_NIEUWE_TEMPLATES', true );
update_option( 'sampark_handwerk', 1, false );
// Het nieuwsarchief toont de berichten in drie kolommen: 9 per keer in plaats van de standaard 10
if ( 10 === (int) get_option( 'posts_per_page' ) ) {
	update_option( 'posts_per_page', 9 );
}
require '/scripts/build-site.php';
