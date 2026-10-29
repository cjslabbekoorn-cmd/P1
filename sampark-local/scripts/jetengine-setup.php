<?php
/**
 * Richt JetEngine in volgens het bouwplan en vult de basisinhoud.
 * Draait via setup.sh (alleen als JetEngine actief is):  wp eval-file /scripts/jetengine-setup.php
 *
 * Gebruikt de eigen tools van JetEngine (MCP-features add-cpt, add-taxonomy, add-glossary, add-query,
 * add-listing, manage-modules) en de dataklassen voor relaties en de Options Page. Zo staat alles
 * in de JetEngine-interface en is het via JetEngine › Dashboard › Skins te exporteren naar staging.
 * Herhaalbaar: wat al bestaat wordt overgeslagen, listing-ontwerpen worden bijgewerkt.
 */

use Jet_Engine\MCP_Tools\Registry;

if ( ! function_exists( 'jet_engine' ) ) {
	WP_CLI::warning( 'JetEngine is niet actief; JetEngine-inrichting overgeslagen.' );
	return;
}

const SP_LISTINGS = '/elementor/listings/';

wp_set_current_user( 1 );
$state = get_option( 'sampark_jet', [] );

function sp_tool( $name, $input ) {
	$feature = Registry::instance()->get_feature( $name );
	if ( ! $feature ) {
		WP_CLI::error( "JetEngine-tool $name niet gevonden" );
	}
	$out = $feature->run( $input );
	if ( is_wp_error( $out ) ) {
		WP_CLI::warning( "$name: " . $out->get_error_message() );
		return null;
	}
	return $out;
}

function sp_field( $name, $title, $type, $extra = [] ) {
	return array_merge( [
		'title' => $title, 'name' => $name, 'object_type' => 'field', 'width' => '100%', 'type' => $type,
		'id' => wp_rand( 10000, 99999 ), 'isNested' => false, 'is_nested' => false, 'options' => [],
		'quick_editable' => true, 'is_required' => false, 'default' => '', 'description' => '',
		'placeholder' => '', 'args' => [], 'conditions' => [], 'repeater-fields' => [],
	], $extra );
}

function sp_db_exists( $type, $slug ) {
	$rows = jet_engine()->db->query( $type, [ 'slug' => $slug ] );
	return ! empty( $rows );
}

// ------------------------------------------------------------------ modules en kaart

sp_tool( 'tool-manage-modules', [ 'operation' => 'activate', 'modules' => [ 'maps-listings', 'dynamic-visibility', 'gallery-grid', 'gallery-slider' ] ] );
sp_tool( 'tool-manage-modules', [ 'operation' => 'deactivate', 'modules' => [ 'booking-forms', 'profile-builder', 'data-stores', 'custom-content-types', 'rest-api-listings', 'calendar', 'qr-code', 'fullwidth-block-editor', 'listing-injections' ] ] );

$maps = get_option( 'jet-engine-maps-settings', [] );
update_option( 'jet-engine-maps-settings', array_merge( is_array( $maps ) ? $maps : [], [
	'map_provider'     => 'leaflet',
	'geocode_provider' => 'openstreetmap',
] ), false );
WP_CLI::log( '  modules en kaart (Leaflet + OpenStreetMap) ingesteld' );

// ------------------------------------------------------------------ glossaries

function sp_glossary( &$state, $key, $name, $fields ) {
	if ( ! empty( $state['glossary'][ $key ] ) ) {
		return;
	}
	$out = sp_tool( 'tool-add-glossary', [ 'name' => $name, 'source' => 'manual', 'fields' => $fields ] );
	$state['glossary'][ $key ] = $out['glossary_id'] ?? $out['item_id'] ?? $out['id'] ?? 0;
	if ( ! $state['glossary'][ $key ] ) {
		foreach ( (array) jet_engine()->glossaries->settings->get() as $g ) {
			if ( ( $g['name'] ?? '' ) === $name ) {
				$state['glossary'][ $key ] = $g['id'];
			}
		}
	}
	WP_CLI::log( "  + glossary $name (" . $state['glossary'][ $key ] . ')' );
}
sp_glossary( $state, 'status', 'Evenementstatus', [
	[ 'value' => 'aangekondigd', 'label' => 'Aangekondigd' ],
	[ 'value' => 'open', 'label' => 'Inschrijving open' ],
	[ 'value' => 'vol', 'label' => 'Vol' ],
	[ 'value' => 'doorlopend', 'label' => 'Het hele jaar' ],
	[ 'value' => 'afgelopen', 'label' => 'Afgelopen' ],
] );
// Labels voor de checklist "Wat Sampark hier betaalt" op de projectsingle
sp_glossary( $state, 'financiering', 'Wat Sampark betaalt', [
	[ 'value' => 'docenten', 'label' => 'Salarissen van docenten' ],
	[ 'value' => 'lesmateriaal', 'label' => 'Lesmateriaal' ],
	[ 'value' => 'sport', 'label' => 'Sportattributen' ],
	[ 'value' => 'schoolarts', 'label' => 'Schoolarts' ],
	[ 'value' => 'gezondheidszorg', 'label' => 'Gezondheidszorg' ],
	[ 'value' => 'fietsen', 'label' => 'Fietsen voor geslaagden' ],
	[ 'value' => 'vaste_lasten', 'label' => 'Vaste lasten zoals elektriciteit' ],
] );
$status_options = [ 'aangekondigd::Aangekondigd', 'open::Inschrijving open', 'vol::Vol', 'doorlopend::Het hele jaar', 'afgelopen::Afgelopen' ];

// ------------------------------------------------------------------ posttypes

$cpts = [
	'projecten' => [
		'general_settings' => [ 'name' => 'Projecten', 'slug' => 'projecten', 'show_edit_link' => true ],
		'labels' => [ 'singular_name' => 'Project', 'menu_name' => 'Projecten', 'add_new_item' => 'Nieuw project' ],
		'advanced_settings' => [ 'has_archive' => false, 'rewrite_slug' => 'ons-werk', 'with_front' => false,
			'menu_icon' => 'dashicons-welcome-learn-more', 'menu_position' => 21,
			'supports' => [ 'title', 'editor', 'thumbnail', 'excerpt', 'page-attributes' ] ],
		'meta_fields' => [
			[ 'name' => 'tagline', 'title' => 'Tagline', 'type' => 'text', 'description' => 'Korte zin onder de titel, bv. "Van vijf lokalen naar vijftien"' ],
			[ 'name' => 'aantal', 'title' => 'Aantal', 'type' => 'number' ],
			[ 'name' => 'eenheid', 'title' => 'Eenheid', 'type' => 'select', 'options' => [ 'leerlingen::leerlingen', 'studenten::studenten', '::geen' ] ],
			[ 'name' => 'soort_werk', 'title' => 'Soort werk', 'type' => 'select', 'options' => [ 'Nieuwbouw::Nieuwbouw', 'Renovatie::Renovatie', 'Doorlopend::Doorlopend' ] ],
			[ 'name' => 'dorp', 'title' => 'Dorp of stad', 'type' => 'text' ],
			sp_field( 'locatie', 'Locatie op de kaart', 'map', [ 'map_value_format' => 'location_string', 'description' => 'Klik de plek aan op de kaart. Wordt gebruikt door de kaart op Ons werk.' ] ),
			[ 'name' => 'feiten', 'title' => 'Feiten (4 stuks)', 'type' => 'repeater', 'fields' => [
				[ 'name' => 'waarde', 'title' => 'Waarde', 'type' => 'text' ],
				[ 'name' => 'label', 'title' => 'Label', 'type' => 'text' ],
			] ],
			[ 'name' => 'extra_titel', 'title' => 'Tweede kop', 'type' => 'text' ],
			[ 'name' => 'extra_tekst', 'title' => 'Tekst bij tweede kop', 'type' => 'textarea' ],
			[ 'name' => 'voorzieningen', 'title' => 'Voorzieningen', 'type' => 'repeater', 'fields' => [
				[ 'name' => 'voorziening', 'title' => 'Voorziening', 'type' => 'text' ],
			] ],
			[ 'name' => 'we_financieren', 'title' => 'Wat Sampark hier betaalt', 'type' => 'checkbox', 'options' => [
				'docenten::Salarissen van docenten', 'lesmateriaal::Lesmateriaal', 'sport::Sportattributen', 'schoolarts::Schoolarts',
				'gezondheidszorg::Gezondheidszorg', 'fietsen::Fietsen voor geslaagden', 'vaste_lasten::Vaste lasten zoals elektriciteit',
			] ],
			[ 'name' => 'momenten', 'title' => 'Momenten', 'type' => 'repeater', 'fields' => [
				[ 'name' => 'moment', 'title' => 'Moment of jaartal', 'type' => 'text' ],
				[ 'name' => 'tekst', 'title' => 'Tekst', 'type' => 'textarea' ],
			] ],
			[ 'name' => 'externe_link', 'title' => 'Externe link (optioneel)', 'type' => 'text' ],
			sp_field( 'galerij', 'Galerij', 'gallery', [ 'value_format' => 'id' ] ),
		],
	],
	'evenementen' => [
		'general_settings' => [ 'name' => 'Evenementen', 'slug' => 'evenementen', 'show_edit_link' => true ],
		'labels' => [ 'singular_name' => 'Evenement', 'menu_name' => 'Evenementen', 'add_new_item' => 'Nieuw evenement' ],
		'advanced_settings' => [ 'has_archive' => false, 'rewrite_slug' => 'evenementen', 'with_front' => false,
			'menu_icon' => 'dashicons-calendar-alt', 'menu_position' => 22, 'supports' => [ 'title', 'editor', 'thumbnail', 'excerpt', 'page-attributes' ] ],
		'meta_fields' => [
			[ 'name' => 'status', 'title' => 'Status', 'type' => 'select', 'options' => $status_options, 'is_required' => true ],
			[ 'name' => 'datum_start', 'title' => 'Datum', 'type' => 'date' ],
			[ 'name' => 'datum_eind', 'title' => 'Einddatum', 'type' => 'date' ],
			[ 'name' => 'datum_label', 'title' => 'Datumtekst (als er nog geen datum is)', 'type' => 'text', 'description' => 'Bv. "Het hele jaar" of "September 2027 · datum volgt"' ],
			[ 'name' => 'inschrijving_tot', 'title' => 'Inschrijven tot', 'type' => 'date' ],
			[ 'name' => 'tijd', 'title' => 'Tijd', 'type' => 'text' ],
			[ 'name' => 'locatie_tekst', 'title' => 'Locatie', 'type' => 'text' ],
			[ 'name' => 'prijs_label', 'title' => 'Prijs', 'type' => 'text' ],
			[ 'name' => 'max_deelnemers', 'title' => 'Maximaal aantal deelnemers', 'type' => 'number' ],
			[ 'name' => 'externe_inschrijflink', 'title' => 'Externe inschrijflink', 'type' => 'text', 'description' => 'Alleen als inschrijven niet via een eigen product gaat (bv. padel via Peakz)' ],
			[ 'name' => 'programma', 'title' => 'Programma', 'type' => 'repeater', 'fields' => [
				[ 'name' => 'tijd', 'title' => 'Tijd', 'type' => 'text' ],
				[ 'name' => 'onderdeel', 'title' => 'Onderdeel', 'type' => 'text' ],
			] ],
			sp_field( 'galerij', 'Galerij', 'gallery', [ 'value_format' => 'id' ] ),
		],
	],
	'sponsors' => [
		'general_settings' => [ 'name' => 'Sponsors', 'slug' => 'sponsors', 'show_edit_link' => true ],
		'labels' => [ 'singular_name' => 'Sponsor', 'menu_name' => 'Sponsors', 'add_new_item' => 'Nieuwe sponsor' ],
		'advanced_settings' => [ 'public' => false, 'publicly_queryable' => false, 'exclude_from_search' => true,
			'show_in_nav_menus' => false, 'has_archive' => false, 'rewrite' => false,
			'menu_icon' => 'dashicons-awards', 'menu_position' => 23, 'supports' => [ 'title', 'thumbnail', 'page-attributes' ] ],
		'meta_fields' => [
			[ 'name' => 'website', 'title' => 'Website', 'type' => 'text' ],
			sp_field( 'actief', 'Toon op de site', 'switcher', [ 'default' => 'true' ] ),
		],
	],
];

foreach ( $cpts as $slug => $input ) {
	if ( post_type_exists( $slug ) || sp_db_exists( 'post_types', $slug ) ) {
		continue;
	}
	$out = sp_tool( 'tool-add-cpt', $input );
	WP_CLI::log( "  + posttype $slug (" . ( $out['item_id'] ?? '?' ) . ')' );
}

// ------------------------------------------------------------------ taxonomieën

$taxes = [
	'projecttype' => [ 'Projecttypes', 'Projecttype', [ 'projecten' ], true ],
	'regio' => [ 'Regio\'s', 'Regio', [ 'projecten' ], true ],
	'sponsorniveau' => [ 'Sponsorniveaus', 'Sponsorniveau', [ 'sponsors' ], false ],
];
foreach ( $taxes as $slug => [ $name, $single, $types, $public ] ) {
	if ( taxonomy_exists( $slug ) || sp_db_exists( 'taxonomies', $slug ) ) {
		continue;
	}
	sp_tool( 'tool-add-taxonomy', [
		'general_settings' => [ 'name' => $name, 'slug' => $slug, 'object_type' => $types ],
		'labels' => [ 'singular_name' => $single, 'menu_name' => $name ],
		'advanced_settings' => [ 'public' => $public, 'publicly_queryable' => false, 'hierarchical' => true, 'show_in_rest' => true, 'rewrite' => false ],
	] );
	WP_CLI::log( "  + taxonomie $slug" );
}

// ------------------------------------------------------------------ Options Page "Stichting"

if ( ! sp_db_exists( 'post_types', 'stichting' ) ) {
	$t = fn( $n, $l, $type = 'text', $e = [] ) => sp_field( $n, $l, $type, $e );
	jet_engine()->options_pages->data->set_request( [
		'name' => 'Stichting', 'slug' => 'stichting', 'menu_name' => 'Stichting', 'icon' => 'dashicons-heart',
		'position' => 3, 'capability' => 'edit_pages', 'storage_type' => 'default', 'option_prefix' => false,
		'meta_fields' => [
			sp_field( 'tab_cijfers', 'Kerncijfers', 'html', [ 'object_type' => 'tab' ] ),
			$t( 'cijfer_leerlingen', 'Leerlingen op onze scholen', 'number' ),
			$t( 'cijfer_cursussen', 'Voltooide cursussen', 'number' ),
			$t( 'cijfer_fietsen', 'Fietsen per jaar', 'number' ),
			$t( 'cijfer_studenten_delhi', 'Studenten in Delhi', 'number' ),
			sp_field( 'tab_contact', 'Contact en registratie', 'html', [ 'object_type' => 'tab' ] ),
			$t( 'adres', 'Adres', 'textarea' ),
			$t( 'telefoon', 'Telefoon' ),
			$t( 'email', 'E-mail' ),
			$t( 'bereikbaarheid', 'Bereikbaarheid' ),
			$t( 'kvk', 'KvK-nummer' ),
			$t( 'rsin', 'RSIN' ),
			$t( 'iban', 'IBAN' ),
			sp_field( 'tab_campagne', 'Campagne', 'html', [ 'object_type' => 'tab' ] ),
			$t( 'campagne_aan', 'Campagnebadge tonen', 'switcher' ),
			$t( 'campagne_titel', 'Titel' ),
			$t( 'campagne_tekst', 'Tekst' ),
			$t( 'campagne_link', 'Link' ),
			sp_field( 'tab_organisatie', 'Organisatie', 'html', [ 'object_type' => 'tab' ] ),
			$t( 'bestuur', 'Bestuur', 'repeater', [ 'repeater-fields' => [
				$t( 'naam', 'Naam' ), $t( 'functie', 'Functie' ), $t( 'foto', 'Foto', 'media', [ 'value_format' => 'id' ] ) ] ] ),
			$t( 'tijdlijn', 'Tijdlijn', 'repeater', [ 'repeater-fields' => [
				$t( 'jaar', 'Jaar' ), $t( 'titel', 'Titel' ), $t( 'tekst', 'Tekst', 'textarea' ) ] ] ),
			sp_field( 'tab_anbi', 'ANBI', 'html', [ 'object_type' => 'tab' ] ),
			$t( 'anbi_beleidsplan', 'Beleidsplan', 'wysiwyg' ),
			$t( 'anbi_beloningsbeleid', 'Beloningsbeleid', 'wysiwyg' ),
			$t( 'anbi_activiteiten', 'Verslag van activiteiten', 'wysiwyg' ),
			$t( 'anbi_documenten', 'Documenten', 'repeater', [ 'repeater-fields' => [
				$t( 'jaar', 'Jaar' ), $t( 'soort', 'Soort' ), $t( 'bestand', 'Bestand', 'media', [ 'value_format' => 'url' ] ) ] ] ),
		],
	] );
	jet_engine()->options_pages->data->create_item( false );
	WP_CLI::log( '  + Options Page Stichting' );
}

// ------------------------------------------------------------------ relaties

$relations = [
	'evenement_product'   => [ 'Evenement → Product', 'posts::evenementen', 'posts::product', 'one_to_many' ],
	'evenement_bericht'   => [ 'Evenement ↔ Bericht', 'posts::evenementen', 'posts::post', 'many_to_many' ],
	'project_bericht'     => [ 'Project ↔ Bericht', 'posts::projecten', 'posts::post', 'many_to_many' ],
	'sponsor_evenement'   => [ 'Sponsor ↔ Evenement', 'posts::sponsors', 'posts::evenementen', 'many_to_many' ],
];
$existing_rel = array_map( function ( $r ) {
	$args = maybe_unserialize( $r['args'] ?? [] );
	return is_array( $args ) ? ( $args['name'] ?? '' ) : '';
}, (array) jet_engine()->relations->data->get_raw() );
foreach ( $relations as $key => [ $name, $parent, $child, $type ] ) {
	if ( in_array( $name, $existing_rel, true ) ) {
		continue;
	}
	jet_engine()->relations->data->set_request( [
		'name' => $name, 'parent_object' => $parent, 'child_object' => $child, 'type' => $type,
		'parent_control' => true, 'child_control' => true, 'parent_manager' => true, 'child_manager' => true,
		'parent_allow_delete' => true, 'child_allow_delete' => true, 'db_table' => false, 'is_legacy' => false,
	] );
	jet_engine()->relations->data->create_item( false );
	WP_CLI::log( "  + relatie $name" );
}

// Registreer wat net is aangemaakt, zodat queries en inhoud er meteen mee werken
jet_engine()->cpt->data->reset_raw_cache();
jet_engine()->taxonomies->data->reset_raw_cache();
foreach ( jet_engine()->cpt->data->get_items() as $item ) {
	if ( ! post_type_exists( $item['slug'] ) ) {
		$reg = jet_engine()->cpt->data->filter_item_for_register( $item );
		register_post_type( $item['slug'], $reg );
	}
}
foreach ( jet_engine()->taxonomies->data->get_items() as $item ) {
	if ( ! taxonomy_exists( $item['slug'] ) ) {
		register_taxonomy( $item['slug'], $item['object_type'], jet_engine()->taxonomies->data->filter_item_for_register( $item ) );
	}
}
update_option( 'sampark_jet', $state, false );

// ------------------------------------------------------------------ inhoud

$content = json_decode( file_get_contents( '/elementor/content.json' ), true );
$media   = get_option( 'sampark_media', [] );
$m       = fn( $key ) => (int) ( $media[ $key ] ?? 0 );

function sp_term( $tax, $slug, $name ) {
	$t = get_term_by( 'slug', $slug, $tax );
	if ( $t ) {
		return $t->term_id;
	}
	$r = wp_insert_term( $name, $tax, [ 'slug' => $slug ] );
	return is_wp_error( $r ) ? 0 : $r['term_id'];
}
foreach ( [ 'school' => 'Scholen', 'opleiding' => 'Opleidingen', 'initiatief' => 'Initiatieven' ] as $s => $n ) {
	sp_term( 'projecttype', $s, $n );
}
sp_term( 'regio', 'budaun', 'Budaun, Uttar Pradesh' );
sp_term( 'regio', 'new-delhi', 'New Delhi' );
foreach ( [ 'sona' => 'Sona (goud)', 'chandee' => 'Chandee (zilver)', 'peetal' => 'Peetal (brons)', 'partner' => 'Partner' ] as $s => $n ) {
	sp_term( 'sponsorniveau', $s, $n );
}

function sp_upsert( $type, $slug, $arr ) {
	$found = get_posts( [ 'post_type' => $type, 'name' => $slug, 'post_status' => 'any', 'numberposts' => 1, 'fields' => 'ids' ] );
	$arr = array_merge( [ 'post_type' => $type, 'post_status' => 'publish', 'post_name' => $slug ], $arr );
	if ( $found ) {
		return $found[0]; // bestaande inhoud niet overschrijven: die kan in de beheeromgeving zijn aangepast
	}
	$id = wp_insert_post( $arr, true );
	return is_wp_error( $id ) ? 0 : $id;
}

$ids = [ 'projecten' => [], 'evenementen' => [], 'post' => [] ];
$map_prefix = md5( 'locatie' );
foreach ( $content['projects'] as $p ) {
	$new = ! get_posts( [ 'post_type' => 'projecten', 'name' => $p['slug'], 'post_status' => 'any', 'fields' => 'ids' ] );
	$id = sp_upsert( 'projecten', $p['slug'], [ 'post_title' => $p['title'], 'post_excerpt' => $p['excerpt'],
		'post_content' => $p['content'], 'menu_order' => $p['order'] ] );
	$ids['projecten'][ $p['slug'] ] = $id;
	if ( ! $id ) {
		continue;
	}
	// Termen altijd (opnieuw) koppelen: in de allereerste ronde is de taxonomie soms nog niet geregistreerd
	if ( ! has_term( '', 'projecttype', $id ) ) {
		wp_set_object_terms( $id, $p['type'], 'projecttype' );
	}
	if ( ! empty( $p['regio'] ) && ! has_term( '', 'regio', $id ) ) {
		wp_set_object_terms( $id, $p['regio'], 'regio' );
	}
	if ( ! $new ) {
		continue;
	}
	foreach ( $p['meta'] as $k => $v ) {
		update_post_meta( $id, $k, $v );
	}
	if ( ! empty( $p['lat'] ) ) {
		$loc = $p['lat'] . ', ' . $p['lng'];
		update_post_meta( $id, 'locatie', $loc );
		update_post_meta( $id, $map_prefix . '_hash', md5( $loc ) );
		update_post_meta( $id, $map_prefix . '_lat', $p['lat'] );
		update_post_meta( $id, $map_prefix . '_lng', $p['lng'] );
	}
	if ( $m( $p['thumb'] ) ) {
		set_post_thumbnail( $id, $m( $p['thumb'] ) );
	}
	update_post_meta( $id, 'galerij', implode( ',', array_filter( array_map( $m, $p['gallery'] ) ) ) );
	WP_CLI::log( "  + project {$p['title']}" );
}

foreach ( $content['events'] as $e ) {
	$new = ! get_posts( [ 'post_type' => 'evenementen', 'name' => $e['slug'], 'post_status' => 'any', 'fields' => 'ids' ] );
	// Volgorde (menu_order) bepaalt de sortering: evenementen zonder vaste datum vallen dan niet weg
	$id = sp_upsert( 'evenementen', $e['slug'], [ 'post_title' => $e['title'], 'post_excerpt' => $e['excerpt'], 'post_content' => $e['content'], 'menu_order' => $e['order'] ?? 0 ] );
	$ids['evenementen'][ $e['slug'] ] = $id;
	if ( ! $id || ! $new ) {
		continue;
	}
	foreach ( $e['meta'] as $k => $v ) {
		// JetEngine bewaart datumvelden als timestamp
		if ( in_array( $k, [ 'datum_start', 'datum_eind', 'inschrijving_tot' ], true ) ) {
			$v = strtotime( $v . ' 12:00:00' );
		}
		update_post_meta( $id, $k, $v );
	}
	if ( $m( $e['thumb'] ) ) {
		set_post_thumbnail( $id, $m( $e['thumb'] ) );
	}
	WP_CLI::log( "  + evenement {$e['title']}" );
}

foreach ( $content['sponsors'] as $s ) {
	$slug = sanitize_title( $s['title'] );
	$new = ! get_posts( [ 'post_type' => 'sponsors', 'name' => $slug, 'post_status' => 'any', 'fields' => 'ids' ] );
	$id = sp_upsert( 'sponsors', $slug, [ 'post_title' => $s['title'], 'menu_order' => $s['order'] ] );
	if ( ! $id || ! $new ) {
		continue;
	}
	update_post_meta( $id, 'website', $s['website'] );
	update_post_meta( $id, 'actief', 'true' );
	if ( $m( $s['thumb'] ) ) {
		set_post_thumbnail( $id, $m( $s['thumb'] ) );
	}
}
WP_CLI::log( '  sponsors: ' . count( $content['sponsors'] ) );

foreach ( $content['news'] as $n ) {
	$new = ! get_posts( [ 'post_type' => 'post', 'name' => $n['slug'], 'post_status' => 'any', 'fields' => 'ids' ] );
	$id = sp_upsert( 'post', $n['slug'], [ 'post_title' => $n['title'], 'post_excerpt' => $n['excerpt'],
		'post_content' => '<p>' . $n['excerpt'] . '</p><p><em>Volledige tekst volgt bij de migratie van live.</em></p>',
		'post_date' => $n['date'] ] );
	$ids['post'][ $n['slug'] ] = $id;
	if ( ! $id || ! $new ) {
		continue;
	}
	$cat = get_term_by( 'slug', $n['cat'], 'category' );
	if ( $cat ) {
		wp_set_post_categories( $id, [ $cat->term_id ] );
	}
	if ( $m( $n['thumb'] ) ) {
		set_post_thumbnail( $id, $m( $n['thumb'] ) );
	}
}

// relaties vullen: berichten aan evenementen en projecten
$rel_by_name = [];
foreach ( jet_engine()->relations->get_active_relations() as $rel_id => $rel ) {
	$rel_by_name[ $rel->get_args( 'name' ) ] = $rel;
}
foreach ( $content['news'] as $n ) {
	$post_id = $ids['post'][ $n['slug'] ] ?? 0;
	foreach ( $n['events'] ?? [] as $ev ) {
		if ( $post_id && ! empty( $ids['evenementen'][ $ev ] ) && isset( $rel_by_name['Evenement ↔ Bericht'] ) ) {
			$rel_by_name['Evenement ↔ Bericht']->update( $ids['evenementen'][ $ev ], $post_id );
		}
	}
	foreach ( $n['projects'] ?? [] as $pr ) {
		if ( $post_id && ! empty( $ids['projecten'][ $pr ] ) && isset( $rel_by_name['Project ↔ Bericht'] ) ) {
			$rel_by_name['Project ↔ Bericht']->update( $ids['projecten'][ $pr ], $post_id );
		}
	}
}

foreach ( $content['events'] as $e ) {
	foreach ( $e['products'] ?? [] as $slug ) {
		$product = get_posts( [ 'post_type' => 'product', 'name' => $slug, 'post_status' => 'any', 'numberposts' => 1, 'fields' => 'ids' ] )
			?: get_posts( [ 'post_type' => 'product', 'post_status' => 'draft', 'title' => ucfirst( str_replace( '-', ' ', $slug ) ), 'numberposts' => 1, 'fields' => 'ids' ] );
		if ( $product && ! empty( $ids['evenementen'][ $e['slug'] ] ) && isset( $rel_by_name['Evenement → Product'] ) ) {
			$rel_by_name['Evenement → Product']->update( $ids['evenementen'][ $e['slug'] ], $product[0] );
		}
	}
}

// Options Page vullen (alleen lege velden)
$opts = get_option( 'stichting', [] );
$opts = is_array( $opts ) ? $opts : [];
foreach ( $content['options'] as $k => $v ) {
	if ( isset( $opts[ $k ] ) && '' !== $opts[ $k ] ) {
		continue;
	}
	if ( is_array( $v ) ) {
		$rows = [];
		foreach ( $v as $i => $row ) {
			if ( isset( $row['foto'] ) ) {
				$row['foto'] = $m( $row['foto'] );
			}
			$rows[ 'item-' . $i ] = $row;
		}
		$v = $rows;
	}
	$opts[ $k ] = $v;
}
update_option( 'stichting', $opts );
WP_CLI::log( '  Options Page Stichting gevuld' );

// ------------------------------------------------------------------ queries

$term_id = fn( $tax, $slug ) => (int) ( get_term_by( 'slug', $slug, $tax )->term_id ?? 0 );
$queries = [
	'q_scholen'          => [ 'Projecten · scholen', 'posts', [ 'post_type' => [ 'projecten' ], 'posts_per_page' => 12, 'orderby' => 'menu_order', 'order' => 'ASC',
		'tax_query' => [ [ 'taxonomy' => 'projecttype', 'field' => 'slug', 'terms' => [ 'school' ] ] ] ] ],
	'q_opleidingen'      => [ 'Projecten · opleidingen', 'posts', [ 'post_type' => [ 'projecten' ], 'posts_per_page' => 12, 'orderby' => 'menu_order', 'order' => 'ASC',
		'tax_query' => [ [ 'taxonomy' => 'projecttype', 'field' => 'slug', 'terms' => [ 'opleiding' ] ] ] ] ],
	'q_initiatieven'     => [ 'Projecten · initiatieven', 'posts', [ 'post_type' => [ 'projecten' ], 'posts_per_page' => 12, 'orderby' => 'menu_order', 'order' => 'ASC',
		'tax_query' => [ [ 'taxonomy' => 'projecttype', 'field' => 'slug', 'terms' => [ 'initiatief' ] ] ] ] ],
	'q_kaart'            => [ 'Projecten · kaart (scholen en opleidingen)', 'posts', [ 'post_type' => [ 'projecten' ], 'posts_per_page' => 50,
		'tax_query' => [ [ 'taxonomy' => 'projecttype', 'field' => 'slug', 'terms' => [ 'school', 'opleiding' ] ] ] ] ],
	'q_events_home'      => [ 'Evenementen · home (max 3)', 'posts', [ 'post_type' => [ 'evenementen' ], 'posts_per_page' => 3,
		'meta_query' => [ [ 'key' => 'status', 'value' => [ 'aangekondigd', 'open', 'vol', 'doorlopend' ], 'compare' => 'IN' ] ],
		'orderby' => 'menu_order', 'order' => 'ASC' ] ],
	'q_events_binnenkort' => [ 'Evenementen · binnenkort', 'posts', [ 'post_type' => [ 'evenementen' ], 'posts_per_page' => 12,
		'meta_query' => [ [ 'key' => 'status', 'value' => [ 'aangekondigd', 'open', 'vol' ], 'compare' => 'IN' ] ],
		'orderby' => 'menu_order', 'order' => 'ASC' ] ],
	'q_events_doorlopend' => [ 'Evenementen · het hele jaar', 'posts', [ 'post_type' => [ 'evenementen' ], 'posts_per_page' => 12,
		'meta_query' => [ [ 'key' => 'status', 'value' => 'doorlopend', 'compare' => '=' ] ] ] ],
	'q_sponsors'         => [ 'Sponsors · logowand', 'posts', [ 'post_type' => [ 'sponsors' ], 'posts_per_page' => 60, 'orderby' => 'menu_order', 'order' => 'ASC',
		'meta_query' => [ [ 'key' => 'actief', 'value' => 'true', 'compare' => '=' ] ] ] ],
	'q_nieuws'           => [ 'Nieuws · 3 nieuwste', 'posts', [ 'post_type' => [ 'post' ], 'posts_per_page' => 3, 'orderby' => 'date', 'order' => 'DESC' ] ],
	'q_nieuws_events'    => [ 'Nieuws · terugblikken evenementen', 'posts', [ 'post_type' => [ 'post' ], 'posts_per_page' => 3, 'orderby' => 'date', 'order' => 'DESC',
		'tax_query' => [ [ 'taxonomy' => 'category', 'field' => 'slug', 'terms' => [ 'evenementen' ] ] ] ] ],
	'q_pakketten'        => [ 'Producten · sponsorpakketten', 'posts', [ 'post_type' => [ 'product' ], 'posts_per_page' => 6,
		'tax_query' => [ [ 'taxonomy' => 'product_cat', 'field' => 'slug', 'terms' => [ 'sponsorpakket' ] ] ],
		'post__not_in' => array_filter( [ (int) ( get_page_by_path( 'sponsor-een-kind', OBJECT, 'product' )->ID ?? 0 ) ] ),
		'orderby' => 'meta_value_num', 'meta_key' => '_price', 'order' => 'DESC' ] ],
];

// Queries voor de single-templates. Ze werken op het bericht dat bekeken wordt, via JetEngine-macro's:
// %current_id%, %current_terms|taxonomie% en %rel_get_items|relatie-ID|wat tonen|current_object%.
$rel = fn( $name, $what ) => isset( $rel_by_name[ $name ] )
	? '%rel_get_items|' . $rel_by_name[ $name ]->get_id() . '|' . $what . '|current_object%' : '';
$queries += [
	'q_dit_project'       => [ 'Single · dit project (kaart)', 'posts', [ 'post_type' => [ 'projecten' ], 'post__in' => '%current_id%', 'posts_per_page' => 1 ] ],
	'q_andere_projecten'  => [ 'Single · andere projecten van hetzelfde type', 'posts', [ 'post_type' => [ 'projecten' ], 'posts_per_page' => 3,
		'post__not_in' => '%current_id%', 'orderby' => 'menu_order', 'order' => 'ASC',
		'tax_query' => [ [ 'taxonomy' => 'projecttype', 'field' => 'term_id', 'terms' => '%current_terms|projecttype%' ] ] ] ],
	'q_project_nieuws'    => [ 'Single · nieuws bij dit project', 'posts', [ 'post_type' => [ 'post' ], 'posts_per_page' => 3,
		'post__in' => $rel( 'Project ↔ Bericht', 'child_object' ), 'orderby' => 'date', 'order' => 'DESC' ] ],
	'q_event_producten'   => [ 'Single · producten bij dit evenement', 'posts', [ 'post_type' => [ 'product' ], 'posts_per_page' => 6,
		'post__in' => $rel( 'Evenement → Product', 'child_object' ), 'orderby' => 'title', 'order' => 'DESC' ] ],
	'q_event_sponsors'    => [ 'Single · sponsors van dit evenement', 'posts', [ 'post_type' => [ 'sponsors' ], 'posts_per_page' => 30,
		'post__in' => $rel( 'Sponsor ↔ Evenement', 'parent_object' ), 'orderby' => 'menu_order', 'order' => 'ASC' ] ],
	'q_event_nieuws'      => [ 'Single · nieuws bij dit evenement', 'posts', [ 'post_type' => [ 'post' ], 'posts_per_page' => 3,
		'post__in' => $rel( 'Evenement ↔ Bericht', 'child_object' ), 'orderby' => 'date', 'order' => 'DESC' ] ],
	'q_bericht_projecten' => [ 'Single · projecten bij dit bericht', 'posts', [ 'post_type' => [ 'projecten' ], 'posts_per_page' => 3,
		'post__in' => $rel( 'Project ↔ Bericht', 'parent_object' ) ] ],
	'q_bericht_events'    => [ 'Single · evenementen bij dit bericht', 'posts', [ 'post_type' => [ 'evenementen' ], 'posts_per_page' => 3,
		'post__in' => $rel( 'Evenement ↔ Bericht', 'parent_object' ) ] ],
	'q_andere_events'     => [ 'Single · andere evenementen (niet afgelopen)', 'posts', [ 'post_type' => [ 'evenementen' ], 'posts_per_page' => 3,
		'post__not_in' => '%current_id%', 'orderby' => 'menu_order', 'order' => 'ASC',
		'meta_query' => [ [ 'key' => 'status', 'value' => [ 'aangekondigd', 'open', 'vol', 'doorlopend' ], 'compare' => 'IN' ] ] ] ],
	'q_nieuws_meer'       => [ 'Single · meer nieuws (zonder dit bericht)', 'posts', [ 'post_type' => [ 'post' ], 'posts_per_page' => 3,
		'post__not_in' => '%current_id%', 'orderby' => 'date', 'order' => 'DESC' ] ],
];
foreach ( $queries as $key => [ $name, $type, $args ] ) {
	if ( ! empty( $state['queries'][ $key ] ) ) {
		continue;
	}
	if ( array_key_exists( 'post__in', $args ) && '' === $args['post__in'] ) {
		WP_CLI::warning( "query $key overgeslagen: relatie nog niet geregistreerd. Draai jetengine-setup.php nog een keer." );
		continue;
	}
	$out = sp_tool( 'tool-add-query', [ 'name' => $name, 'query_type' => $type, 'query_args' => $args ] );
	$qid = $out['query_id'] ?? $out['item_id'] ?? $out['id'] ?? 0;
	if ( $qid ) {
		$state['queries'][ $key ] = (int) $qid;
		WP_CLI::log( "  + query $name ($qid)" );
	} else {
		WP_CLI::warning( "query $key: " . wp_json_encode( $out ) );
	}
}

// De MCP-converter van JetEngine 3.8.10 slaat lege dynamische tax-clauses op als stdClass (fatal bij gebruik)
// en neemt meta_key niet over in de sortering. Dat herstellen we direct in de opgeslagen query.
function sp_fix_query( $qid, $meta_key = '', $post_in = '' ) {
	global $wpdb;
	$table = $wpdb->prefix . 'jet_post_types';
	$raw   = $wpdb->get_var( $wpdb->prepare( "SELECT args FROM $table WHERE id = %d", $qid ) );
	$args  = maybe_unserialize( $raw );
	if ( ! is_array( $args ) ) {
		return;
	}
	foreach ( $args as $k => $v ) {
		if ( str_starts_with( $k, '__dynamic_' ) && is_array( $v ) ) {
			foreach ( $v as $clause => $rows ) {
				if ( is_array( $rows ) ) {
					foreach ( $rows as $rid => $row ) {
						if ( is_object( $row ) ) {
							$args[ $k ][ $clause ][ $rid ] = (array) $row;
						}
					}
				}
			}
		}
	}
	// Relatie-queries die bij de eerste run zijn aangemaakt voordat JetEngine de relaties kende, missen hun filter
	// (post__in leeg) en tonen dan alle producten of berichten: zet de macro er alsnog in
	if ( $post_in && ( $args['posts']['post__in'] ?? '' ) !== $post_in ) {
		$args['posts']['post__in'] = $post_in;
		WP_CLI::log( "  ~ query $qid: filter op relatie hersteld" );
	}
	// Macro's (%current_id% enz.) werkt JetEngine alleen uit als ze ook in de dynamische index staan,
	// zoals de interface dat doet bij het kiezen van een macro
	$dyn = (array) ( $args['__dynamic_posts'] ?? [] );
	foreach ( (array) ( $args['posts'] ?? [] ) as $k => $v ) {
		if ( is_string( $v ) && preg_match( '/^%[a-z_]+(\|[^%]*)?%$/', $v ) ) {
			$dyn[ $k ] = $v;
		}
	}
	foreach ( (array) ( $args['posts']['tax_query'] ?? [] ) as $row ) {
		if ( isset( $row['_id'] ) && is_string( $row['terms'] ?? null ) && str_starts_with( $row['terms'], '%' ) ) {
			$dyn['tax_query'] = (array) ( $dyn['tax_query'] ?? [] );
			$dyn['tax_query'][ $row['_id'] ] = [ 'terms' => $row['terms'] ];
		}
	}
	if ( $dyn ) {
		$args['__dynamic_posts'] = $dyn;
	}
	if ( $meta_key && ! empty( $args['posts']['orderby'] ) ) {
		foreach ( $args['posts']['orderby'] as $i => $row ) {
			if ( in_array( $row['orderby'] ?? '', [ 'meta_value', 'meta_value_num' ], true ) ) {
				$args['posts']['orderby'][ $i ]['meta_key'] = $meta_key;
			}
		}
	}
	$wpdb->update( $table, [ 'args' => maybe_serialize( $args ) ], [ 'id' => $qid ] );
}
foreach ( $queries as $key => [ $name, $type, $args ] ) {
	if ( ! empty( $state['queries'][ $key ] ) ) {
		$post_in = is_string( $args['post__in'] ?? null ) && str_starts_with( $args['post__in'], '%rel_get_items' ) ? $args['post__in'] : '';
		sp_fix_query( $state['queries'][ $key ], $args['meta_key'] ?? '', $post_in );
	}
}

// ------------------------------------------------------------------ listings

$listing_query = [ 'projectkaart' => 'q_scholen', 'eventkaart' => 'q_events_binnenkort', 'sponsorlogo' => 'q_sponsors',
	'nieuwskaart' => 'q_nieuws', 'pakketkaart' => 'q_pakketten', 'kaartpopup' => 'q_kaart',
	'inschrijfkaart' => 'q_event_producten', 'inschrijfkaart-groot' => 'q_event_producten', 'bestelkaart' => 'q_event_producten' ];
foreach ( glob( SP_LISTINGS . '*.json' ) as $file ) {
	$doc = json_decode( file_get_contents( $file ), true );
	$key = $doc['key'];
	$lid     = (int) ( $state['listings'][ $key ] ?? 0 );
	$created = false;
	if ( ! $lid || ! get_post( $lid ) ) {
		$existing = get_posts( [ 'post_type' => jet_engine()->post_type->slug(), 'title' => $doc['title'], 'post_status' => 'any', 'numberposts' => 1, 'fields' => 'ids' ] );
		$lid = $existing ? $existing[0] : 0;
	}
	if ( ! $lid ) {
		// Zelfde aanroep als de JetEngine-interface (Listings › Nieuw), zonder de MCP-tool die de query uitvoert
		$req = [ 'listing_source' => 'posts', 'listing_post_type' => $doc['source'], 'listing_tax' => 'category',
			'_query_id' => $state['queries'][ $listing_query[ $key ] ] ?? '', 'repeater_source' => 'jet_engine',
			'template_name' => $doc['title'], 'listing_view_type' => 'elementor', '_is_ajax_form' => true,
			'template_entry_type' => 'listing' ];
		$backup = $_REQUEST;
		$_REQUEST = array_merge( $_REQUEST, $req );
		$tpl = jet_engine()->listings->post_type->admin_screen->create_listing_template( $req );
		$_REQUEST = $backup;
		$lid = (int) ( $tpl['template_id'] ?? 0 );
		if ( ! $lid ) {
			WP_CLI::warning( "listing $key niet aangemaakt" );
			continue;
		}
		WP_CLI::log( "  + listing {$doc['title']} ($lid)" );
		$created = true;
	}
	$is_new = $created || empty( $state['listings'][ $key ] );
	$state['listings'][ $key ] = $lid;
	update_option( 'sampark_jet', $state, false );
	if ( ! $is_new && get_option( 'sampark_handwerk' ) ) {
		continue; // bestaande listing kan met de hand zijn aangepast
	}
	$json = wp_json_encode( $doc['content'], JSON_UNESCAPED_UNICODE );
	$json = str_replace( '{{glossary:status}}', (string) ( $state['glossary']['status'] ?? '' ), $json );
	update_post_meta( $lid, '_elementor_data', wp_slash( $json ) );
	update_post_meta( $lid, '_elementor_edit_mode', 'builder' );
}

update_option( 'sampark_jet', $state, false );
if ( class_exists( '\Elementor\Plugin' ) ) {
	\Elementor\Plugin::$instance->files_manager->clear_cache();
}
