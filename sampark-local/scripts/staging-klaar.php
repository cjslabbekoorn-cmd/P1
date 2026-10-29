<?php
/**
 * Maakt de lokale site klaar voor de overstap naar staging en controleert wat er nog openstaat.
 *
 *   docker compose run --rm wpcli eval-file /scripts/staging-klaar.php
 *
 * Wat het doet (veilig om vaker te draaien):
 * - zet de CSS uit mu-plugins/sampark-styles.css in Elementor › Site-instellingen › Aangepaste CSS
 *   (de mu-plugin draait alleen in Docker; daarna laadt hij de CSS niet meer dubbel)
 * - zet de redirects uit content/redirects.csv in Redirection (gaan zo mee naar staging en live)
 * - zoekmachines blokkeren (staging hoort niet in Google; bij de livegang weer aan)
 * - Elementor-CSS opnieuw genereren
 *
 * Testbestellingen, testklanten en formulierinzendingen opruimen (pas vlak voor de export):
 *   docker compose run --rm wpcli eval-file /scripts/staging-klaar.php --exec="define('SP_OPRUIMEN', true);"
 *
 * Daarna een lijst met controles: ✔ in orde, ! let op, ✖ moet nog.
 */

$ok = $let = $mis = 0;
$check = function ( $status, $msg ) use ( &$ok, &$let, &$mis ) {
	$icon = [ 'ok' => '✔', 'let' => '!', 'mis' => '✖' ][ $status ];
	${ $status }++;
	WP_CLI::log( "  $icon $msg" );
};

// ------------------------------------------------------------------ 1. CSS naar Elementor
WP_CLI::log( 'Klaarzetten' );
$css_file = WP_CONTENT_DIR . '/mu-plugins/sampark-styles.css';
$kit_id   = (int) get_option( 'elementor_active_kit' );
if ( ! $kit_id || ! is_readable( $css_file ) ) {
	WP_CLI::warning( 'Elementor-kit of sampark-styles.css niet gevonden; CSS niet overgezet.' );
} else {
	$set   = get_post_meta( $kit_id, '_elementor_page_settings', true );
	$set   = is_array( $set ) ? $set : [];
	$block = "/* sampark-styles begin */\n" . trim( file_get_contents( $css_file ) ) . "\n/* sampark-styles einde */";
	$old   = (string) ( $set['custom_css'] ?? '' );
	// eigen CSS die er al met de hand in staat blijft staan; alleen ons blok wordt vervangen
	$new = preg_match( '#/\* sampark-styles begin \*/.*?/\* sampark-styles einde \*/#s', $old )
		? preg_replace( '#/\* sampark-styles begin \*/.*?/\* sampark-styles einde \*/#s', addcslashes( $block, '\\$' ), $old )
		: trim( $old . "\n\n" . $block );
	if ( $new !== $old ) {
		$set['custom_css'] = $new;
		update_post_meta( $kit_id, '_elementor_page_settings', wp_slash( $set ) );
		WP_CLI::log( '  + CSS in Elementor › Site-instellingen › Aangepaste CSS gezet' );
	}
}

// ------------------------------------------------------------------ 2. redirects in Redirection
global $wpdb;
$csv = '/content/redirects.csv';
if ( is_plugin_active( 'redirection/redirection.php' ) && is_readable( $csv ) ) {
	// Redirection maakt zijn tabellen pas bij het eerste bezoek aan de beheerpagina; dat doen we hier
	if ( ! $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $wpdb->prefix . 'redirection_items' ) ) ) {
		WP_CLI::runcommand( 'redirection database install', [ 'return' => true ] );
		WP_CLI::log( '  + Redirection geïnstalleerd' );
	}
	$before = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->prefix}redirection_items" );
	WP_CLI::runcommand( 'redirection import ' . $csv . ' --format=csv --duplicate-mode=ignore', [ 'return' => true ] );
	$added = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->prefix}redirection_items" ) - $before;
	if ( $added ) {
		WP_CLI::log( "  + $added redirects in Redirection gezet" );
	}
}

// ------------------------------------------------------------------ 3. zoekmachines blokkeren
if ( '0' !== (string) get_option( 'blog_public' ) ) {
	update_option( 'blog_public', '0' );
	WP_CLI::log( '  + zoekmachines geblokkeerd (Instellingen › Lezen); bij de livegang weer aanzetten' );
}

// ------------------------------------------------------------------ 4. opruimen (alleen op verzoek)
if ( defined( 'SP_OPRUIMEN' ) && SP_OPRUIMEN ) {
	$orders = wc_get_orders( [ 'limit' => -1, 'return' => 'ids', 'status' => array_keys( wc_get_order_statuses() ) ] );
	foreach ( $orders as $oid ) {
		wc_get_order( $oid )->delete( true );
	}
	$customers = get_users( [ 'role' => 'customer', 'fields' => 'ID' ] );
	require_once ABSPATH . 'wp-admin/includes/user.php';
	foreach ( $customers as $uid ) {
		wp_delete_user( $uid );
	}
	$entries = get_posts( [ 'post_type' => 'super_contact_entry', 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids' ] );
	foreach ( $entries as $eid ) {
		wp_delete_post( $eid, true );
	}
	WP_CLI::log( sprintf( '  + opgeruimd: %d bestellingen, %d klanten, %d formulierinzendingen', count( $orders ), count( $customers ), count( $entries ) ) );
}

if ( class_exists( '\Elementor\Plugin' ) ) {
	\Elementor\Plugin::$instance->files_manager->clear_cache();
}

// ------------------------------------------------------------------ controles
WP_CLI::log( '' );
WP_CLI::log( 'Controles' );

// plugins die meegaan
$need = [ 'elementor', 'elementor-pro', 'jet-engine', 'woocommerce', 'super-forms', 'code-snippets', 'wordpress-seo',
	'redirection', 'duracelltomi-google-tag-manager', 'mailchimp-for-woocommerce' ];
$inactive = array_filter( $need, fn( $p ) => ! is_plugin_active( "$p/" . ( [ 'super-forms' => 'super-forms.php',
	'duracelltomi-google-tag-manager' => 'duracelltomi-google-tag-manager-for-wordpress.php' ][ $p ] ?? "$p.php" ) )
	&& ! array_filter( array_keys( get_plugins() ), fn( $f ) => str_starts_with( $f, "$p/" ) && is_plugin_active( $f ) ) );
$inactive ? $check( 'mis', 'plugins niet actief: ' . implode( ', ', $inactive ) ) : $check( 'ok', 'alle plugins actief (' . count( $need ) . ')' );

// snippets
if ( function_exists( '\Code_Snippets\get_snippets' ) ) {
	$snips = array_filter( \Code_Snippets\get_snippets(), fn( $s ) => str_starts_with( $s->name, 'Sampark' ) );
	$off   = array_filter( $snips, fn( $s ) => ! $s->active );
	$off ? $check( 'mis', 'snippets uit: ' . implode( ', ', array_map( fn( $s ) => $s->name, $off ) ) )
		: $check( 'ok', count( $snips ) . ' Sampark-snippets actief' );
}

// CSS
$set = get_post_meta( $kit_id, '_elementor_page_settings', true );
str_contains( (string) ( $set['custom_css'] ?? '' ), '/* sampark-styles begin */' )
	? $check( 'ok', 'sampark-CSS staat in Elementor › Site-instellingen' )
	: $check( 'mis', 'sampark-CSS staat nog niet in Elementor' );
if ( ! get_option( 'elementor_typekit-kit-id' ) ) {
	$check( 'mis', 'Adobe Fonts-project (Aptos) niet ingesteld: Elementor › Instellingen › Integraties' );
}

// WooCommerce-pagina's
$pages = [ 'woocommerce_cart_page_id' => 'winkelwagen', 'woocommerce_checkout_page_id' => 'afrekenen',
	'woocommerce_myaccount_page_id' => 'mijn-account', 'elementor_woocommerce_purchase_summary_page_id' => 'bedankt' ];
$wrong = [];
foreach ( $pages as $opt => $slug ) {
	$p = get_post( (int) get_option( $opt ) );
	if ( ! $p || $p->post_name !== $slug || 'publish' !== $p->post_status ) {
		$wrong[] = "/$slug/";
	}
}
get_page_by_path( 'betaling-mislukt' ) || $wrong[] = '/betaling-mislukt/';
$wrong ? $check( 'mis', 'winkelpagina\'s niet goed ingesteld: ' . implode( ', ', $wrong ) ) : $check( 'ok', 'winkelwagen, afrekenen, mijn account, bedankt en betaling mislukt ingesteld' );
get_option( 'woocommerce_terms_page_id' ) ? $check( 'ok', 'algemene voorwaarden gekoppeld aan het afrekenen' )
	: $check( 'let', 'geen pagina algemene voorwaarden gekoppeld (WooCommerce › Instellingen › Geavanceerd)' );

// betaalmethoden
$gw = WC()->payment_gateways()->payment_gateways();
$on = array_keys( array_filter( $gw, fn( $g ) => 'yes' === $g->enabled ) );
$check( in_array( 'bacs', $on, true ) && in_array( 'cheque', $on, true ) ? 'ok' : 'mis',
	'betaalmethoden aan: ' . implode( ', ', $on ) . ' (Mollie/iDEAL komt erbij op staging)' );

// redirects
if ( class_exists( 'Red_Item' ) ) {
	global $wpdb;
	$n = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->prefix}redirection_items WHERE status = 'enabled'" );
	$check( $n ? 'ok' : 'mis', "$n redirects in Redirection" );
}

// zoekmachines
'0' === (string) get_option( 'blog_public' ) ? $check( 'ok', 'zoekmachines geblokkeerd' ) : $check( 'mis', 'zoekmachines niet geblokkeerd' );

// verwijzingen die na de overstap breken
global $wpdb;
$home = wp_parse_url( home_url() );
$home = $home['host'] . ( isset( $home['port'] ) ? ':' . $home['port'] : '' );
$hosts = [];
foreach ( $wpdb->get_col( "SELECT meta_value FROM {$wpdb->postmeta} WHERE meta_value LIKE '%localhost%' OR meta_value LIKE '%127.0.0.1%'
	UNION ALL SELECT post_content FROM {$wpdb->posts} WHERE post_content LIKE '%localhost%' OR post_content LIKE '%127.0.0.1%'
	UNION ALL SELECT option_value FROM {$wpdb->options} WHERE option_name NOT LIKE '\\_%' AND ( option_value LIKE '%localhost%' OR option_value LIKE '%127.0.0.1%' )" ) as $v ) {
	preg_match_all( '#//(localhost|127\.0\.0\.1)(:\d+)?#', str_replace( '\\/', '/', $v ), $m );
	foreach ( $m[0] as $h ) {
		$h = substr( $h, 2 );
		if ( $h !== $home ) {
			$hosts[ $h ] = ( $hosts[ $h ] ?? 0 ) + 1;
		}
	}
}
$bad = [
	'adressen naar een ander lokaal adres dan ' . $home . ( $hosts ? ' (' . implode( ', ', array_keys( $hosts ) ) . ')' : '' ) => array_sum( $hosts ),
	'afbeeldingen die nog van staging of live komen' => $wpdb->get_var(
		"SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_status = 'publish' AND post_content REGEXP 'stichtingsampark\\\\.nl/wp-content/uploads'" )
		+ $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_elementor_data' AND meta_value REGEXP 'stichtingsampark\\\\.nl(\\\\\\\\)?/wp-content(\\\\\\\\)?/uploads'" ),
];
foreach ( $bad as $what => $n ) {
	$n ? $check( 'mis', "$n $what" ) : $check( 'ok', "geen $what" );
}

// placeholders en lege inhoud
$ph = $wpdb->get_col( "SELECT p.post_title FROM {$wpdb->posts} p LEFT JOIN {$wpdb->postmeta} m ON m.post_id = p.ID AND m.meta_key = '_elementor_data'
	WHERE p.post_status = 'publish' AND p.post_type IN ('page','post','evenementen','projecten','product')
	AND ( p.post_content REGEXP 'lorem ipsum|Voeg je koptekst|TODO' OR m.meta_value REGEXP 'lorem ipsum|Voeg je koptekst|TODO' )" );
$ph ? $check( 'let', 'tijdelijke tekst op: ' . implode( ', ', $ph ) ) : $check( 'ok', 'geen lorem ipsum of tijdelijke teksten' );
$privacy = get_post( (int) get_option( 'wp_page_for_privacy_policy' ) );
( ! $privacy || str_contains( $privacy->post_content, 'Suggestie tekst' ) || str_contains( $privacy->post_content, 'Suggested text' ) || str_contains( $privacy->post_content, 'Wie we zijn' ) )
	? $check( 'let', 'privacyverklaring is nog de standaardtekst van WordPress' )
	: $check( 'ok', 'privacyverklaring ingevuld' );
$nothumb = get_posts( [ 'post_type' => [ 'evenementen', 'projecten', 'product', 'post' ], 'numberposts' => -1, 'fields' => 'ids',
	'meta_query' => [ [ 'key' => '_thumbnail_id', 'compare' => 'NOT EXISTS' ] ] ] );
$nothumb ? $check( 'let', count( $nothumb ) . ' item(s) zonder uitgelichte afbeelding: ' . implode( ', ', array_map( 'get_the_title', array_slice( $nothumb, 0, 8 ) ) ) )
	: $check( 'ok', 'alle projecten, evenementen, producten en berichten hebben een afbeelding' );

// kopieën van templates (SP_VERVANG)
$copies = get_posts( [ 'post_type' => 'elementor_library', 'post_status' => 'draft', 'numberposts' => -1, 's' => '(kopie' ] );
$copies ? $check( 'let', count( $copies ) . ' bewaarde templatekopie(ën) als concept; weggooien als je ze niet meer nodig hebt' )
	: $check( 'ok', 'geen oude templatekopieën' );

// testdata
$orders = count( wc_get_orders( [ 'limit' => -1, 'return' => 'ids' ] ) );
$cust   = count( get_users( [ 'role' => 'customer', 'fields' => 'ID' ] ) );
$orders || $cust ? $check( 'let', "$orders testbestelling(en) en $cust testklant(en); opruimen met SP_OPRUIMEN vlak voor de export" )
	: $check( 'ok', 'geen testbestellingen of testklanten' );

// beheerder
get_user_by( 'login', 'admin' ) ? $check( 'let', 'gebruiker admin bestaat nog: op staging direct een eigen beheerder maken en admin verwijderen' )
	: $check( 'ok', 'geen gebruiker admin' );

// omvang voor de export
$up = 0;
foreach ( new RecursiveIteratorIterator( new RecursiveDirectoryIterator( wp_upload_dir()['basedir'], FilesystemIterator::SKIP_DOTS ) ) as $f ) {
	$up += $f->getSize();
}
$db = (float) $wpdb->get_var( $wpdb->prepare( 'SELECT SUM(data_length + index_length) FROM information_schema.tables WHERE table_schema = %s', DB_NAME ) );
$check( 'ok', sprintf( 'omvang export ongeveer %d MB (uploads %d MB, database %d MB)', ( $up + $db ) / 1048576, $up / 1048576, $db / 1048576 ) );

WP_CLI::log( '' );
$mis ? WP_CLI::warning( "$mis punt(en) moeten nog, $let om op te letten, $ok in orde." )
	: WP_CLI::success( "Klaar voor staging: $ok in orde, $let om op te letten." );
