<?php
/**
 * Zet huisstijl (Elementor-kit), beelden en pagina's van de nieuwe Sampark-site neer.
 * Draait via setup.sh:  wp eval-file /scripts/build-site.php
 * Herhaalbaar: beelden worden één keer geïmporteerd, pagina's worden bijgewerkt.
 */

require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/media.php';
require_once ABSPATH . 'wp-admin/includes/image.php';

// Alleen nieuwe templates toevoegen (scripts/templates-add.php): pagina's, kit en bestaande templates blijven ongemoeid
$only_templates = defined( 'SP_ALLEEN_NIEUWE_TEMPLATES' ) && SP_ALLEEN_NIEUWE_TEMPLATES;

// Na de eerste opbouw wordt de site met de hand in Elementor verder gebouwd. Een volledige run zou die pagina's
// overschrijven, dus dat kan alleen nog bewust: --exec="define('SP_FORCE', true);"
if ( ! $only_templates && get_option( 'sampark_handwerk' ) && ! defined( 'SP_FORCE' ) ) {
	WP_CLI::error( "Deze site wordt met de hand verder gebouwd; build-site.php zou pagina's en templates overschrijven.\n" .
		"Nieuwe templates toevoegen:  wp eval-file /scripts/templates-add.php\n" .
		"Toch alles opnieuw opbouwen: wp eval-file /scripts/build-site.php --exec=\"define('SP_FORCE', true);\"" );
}

const SP_STAGING  = 'https://staging.stichtingsampark.nl/wp-content/uploads/';
const SP_ICONS    = '/assets/icons/';
const SP_PAGES    = '/elementor/pages/';

// ------------------------------------------------------------------ beelden

// SVG's toestaan tijdens de import (Elementor rendert ze inline in het Icon-widget).
update_option( 'elementor_unfiltered_files_upload', 1 );
add_filter( 'upload_mimes', fn( $m ) => $m + [ 'svg' => 'image/svg+xml', 'webp' => 'image/webp' ] );
add_filter( 'wp_check_filetype_and_ext', function ( $data, $file, $filename ) {
	if ( str_ends_with( strtolower( $filename ), '.svg' ) ) {
		return [ 'ext' => 'svg', 'type' => 'image/svg+xml', 'proper_filename' => $filename ];
	}
	return $data;
}, 10, 3 );

$sp_images = [
	// hero's
	'hero_home'        => '2026/07/stichting-sampark-help-een-kind-naar-school-scaled.jpg',
	'hero_onswerk'     => '2026/07/INDIA_EXPORT-121-scaled.jpg',
	'hero_events'      => '2025/09/20.png',
	'hero_steun'       => '2026/07/nehal-patel-aho7nVdauuc-unsplash-scaled.jpg',
	'hero_doneer'      => '2020/10/Header6-25.png',
	'hero_bedrijven'   => '2020/10/IMG_20200210_103516-scaled.jpg',
	'hero_over'        => '2020/10/Header14-25.png',
	'hero_anbi'        => '2020/10/Gdya-8-scaled.jpg',
	'hero_contact'     => '2020/10/Kundanpur-4-1.jpg',
	// projecten
	'proj_khukdi'        => '2020/10/PHOTO-2019-10-01-10-52-45-5.jpg',
	'proj_khukdi_gebouw' => '2020/10/Solarlight-distribution-Ghadia-scaled.jpg',
	'proj_kundanpur'     => '2020/10/Kundanpur-4-1.jpg',
	'proj_bilsi'         => '2020/10/Bilsi-35-scaled.jpg',
	'proj_ghadia'        => '2020/10/Gdya-8-scaled.jpg',
	'proj_computer'      => '2020/10/Computer-centre-4.jpg',
	'proj_modinette'     => '2020/10/Sewing-centre-5.jpg',
	'proj_beauty'        => '2020/10/Beautician-2.jpg',
	'proj_fietsen'       => '2020/10/IMG_0442.jpg',
	'proj_zon'           => '2020/10/Update_zonnepanelen2.jpg',
	'proj_solar'         => '2020/10/Solarlight-distribution-Ghadia-scaled.jpg',
	'proj_accrete'       => '2020/10/Header14-25.png',
	// evenementen en nieuws
	'event_padel'      => '2026/07/INDIA_EXPORT-121-scaled.jpg',
	'event_wijn'       => '2024/10/2025-Sampark-Wijnen.png',
	'event_rally'      => '2025/09/20.png',
	'event_golf'       => '2025/11/Ontwerp-zonder-titel1.png',
	'event_reis'       => '2020/10/IMG_20200210_103516-scaled.jpg',
	'news_golf_2025'   => '2025/11/Ontwerp-zonder-titel1.png',
	'news_canada'      => '2025/09/Ontwerp-zonder-titel23.png',
	'news_abhishek'    => '2025/09/Ontwerp-zonder-titel24.png',
	// steun ons / over ons
	'steun_doneer'     => '2026/07/nehal-patel-aho7nVdauuc-unsplash-scaled.jpg',
	'steun_kind'       => '2020/10/Header6-25.png',
	'steun_bedrijf'    => '2020/10/IMG_20200210_103516-scaled.jpg',
	'steun_event'      => '2025/09/20.png',
	'over_verhaal'     => '2020/10/Bilsi-35-scaled.jpg',
	'board_irma'       => '2020/10/irma.png',
	'board_lianne'     => '2020/10/lianne.png',
	'board_pieter'     => '2020/10/pieter.png',
	'board_arjen'      => '2020/10/arjan.png',
	'board_henk'       => '2020/10/henk.png',
	'board_margreet'   => '2020/10/margreet.png',
	'board_richard'    => '2025/12/Richard-Nijhof-1.png',
	'board_eric'       => '2025/12/Eric-Haasjes.png',
	// logo's
	'logo_sampark'     => '2020/09/StichtingSampark-logo_medium-1.png',
	'logo_anbi'        => '2022/06/Anbi.webp',
	'logo_venture'     => '2022/08/Ontwerp-zonder-titel.png',
	'logo_groothuis'   => '2020/10/Groothuis-Bouwgroep.png',
	'logo_schieven'    => '2026/07/schieven-keizer.svg',
	'logo_w4y'         => '2020/10/W4Y.png',
	'logo_venttri'     => '2020/10/Venttri.jpg',
	'logo_rijk'        => '2020/10/Rijk-van-Nunspeet-768x768-1.jpg',
	'logo_arcus'       => '2020/10/Arcus-IT.png',
	'logo_kvs'         => '2022/08/KVS-logo.png',
	'logo_pleijsier'   => '2020/10/Pleijsier-onderhoud-en-bouw.png',
	'logo_positie1'    => '2022/08/logo-positie1-2019.png',
	// iconen uit de huisstijl (lokaal in assets/icons)
	'icon_rugtas'      => 'local:rugtas.svg',
	'icon_computer'    => 'local:computer.svg',
	'icon_fiets'       => 'local:fiets.svg',
	'icon_wijn'        => 'local:wijn.svg',
	'icon_auto'        => 'local:auto.svg',
	'icon_golf'        => 'local:golf.svg',
	'icon_cultuur'     => 'local:cultuur.svg',
];

$media = get_option( 'sampark_media', [] );
$by_src = [];
foreach ( $sp_images as $key => $src ) {
	if ( ! empty( $media[ $key ] ) && get_post( $media[ $key ] ) ) {
		$by_src[ $src ] = $media[ $key ];
		continue;
	}
	if ( isset( $by_src[ $src ] ) ) {
		$media[ $key ] = $by_src[ $src ];
		continue;
	}
	if ( str_starts_with( $src, 'local:' ) ) {
		$tmp = wp_tempnam( basename( $src ) );
		copy( SP_ICONS . substr( $src, 6 ), $tmp );
		$name = substr( $src, 6 );
	} else {
		$tmp = download_url( SP_STAGING . $src, 120 );
		$name = basename( $src );
	}
	if ( is_wp_error( $tmp ) ) {
		WP_CLI::warning( "Beeld $key niet geladen: " . $tmp->get_error_message() );
		continue;
	}
	$id = media_handle_sideload( [ 'name' => $name, 'tmp_name' => $tmp ], 0, $key );
	if ( is_wp_error( $id ) ) {
		WP_CLI::warning( "Beeld $key niet geïmporteerd: " . $id->get_error_message() );
		@unlink( $tmp );
		continue;
	}
	$media[ $key ] = $id;
	$by_src[ $src ] = $id;
	WP_CLI::log( "  + beeld $key ($id)" );
}
update_option( 'sampark_media', $media, false );

if ( ! $only_templates ) {
// ------------------------------------------------------------------ huisstijl (Elementor-kit)

$kit_id = (int) get_option( 'elementor_active_kit' );
if ( ! $kit_id && class_exists( '\Elementor\Plugin' ) ) {
	$kit_id = \Elementor\Plugin::$instance->kits_manager->create_default();
	update_option( 'elementor_active_kit', $kit_id );
}

$d  = fn( $t, $r = null, $b = null, $l = null, $u = 'px' ) => [
	'unit' => $u, 'top' => (string) $t, 'right' => (string) ( $r ?? $t ), 'bottom' => (string) ( $b ?? $t ),
	'left' => (string) ( $l ?? $r ?? $t ), 'isLinked' => $r === null,
];
$s  = fn( $v, $u = 'px' ) => [ 'unit' => $u, 'size' => $v, 'sizes' => [] ];
$ty = function ( $prefix, $family, $weight, $size = null, $lh = null, $extra = [] ) use ( $s ) {
	$out = [ "{$prefix}_typography" => 'custom', "{$prefix}_font_family" => $family, "{$prefix}_font_weight" => (string) $weight ];
	if ( $size ) {
		$out[ "{$prefix}_font_size" ] = $s( $size[0] );
		$out[ "{$prefix}_font_size_tablet" ] = $s( $size[1] );
		$out[ "{$prefix}_font_size_mobile" ] = $s( $size[2] );
	}
	if ( $lh ) {
		$out[ "{$prefix}_line_height" ] = $s( $lh, 'em' );
	}
	foreach ( $extra as $k => $v ) {
		$out[ "{$prefix}_{$k}" ] = $v;
	}
	return $out;
};

// Waarden 1-op-1 van staging (post-5.css), aangevuld met de huisstijl. Legacy-kleuren van de
// oude site (#DE7A2F, #D6E9EC, #D64D3B, #91B7B6, #FBCDB4, #E7E1D1) zijn bewust weggelaten.
$kit = [
	'system_colors' => [
		[ '_id' => 'primary', 'title' => 'Steenrood', 'color' => '#963322' ],
		[ '_id' => 'secondary', 'title' => 'Oranje', 'color' => '#ED7404' ],
		[ '_id' => 'text', 'title' => 'Donkerbruin (tekst)', 'color' => '#46211A' ],
		[ '_id' => 'accent', 'title' => 'Terracotta', 'color' => '#BD5C38' ],
	],
	'custom_colors' => [
		[ '_id' => '658acb6', 'title' => 'Crème', 'color' => '#F5EDE3' ],
		[ '_id' => 'cf55c96', 'title' => 'Zachtroze', 'color' => '#ECC0AE' ],
		[ '_id' => 'e64974d', 'title' => 'Wit', 'color' => '#FFFFFF' ],
		[ '_id' => '6ff6927', 'title' => 'Logoblauw', 'color' => '#0A285A' ],
	],
	'system_typography' => [
		[ '_id' => 'primary', 'title' => 'Titels (Spectral)' ] + $ty( 'typography', 'Spectral', 500 ),
		[ '_id' => 'secondary', 'title' => 'Knoppen (Patrick Hand)' ] + $ty( 'typography', 'Patrick Hand', 400, null, null, [ 'text_transform' => 'uppercase' ] ),
		[ '_id' => 'text', 'title' => 'Tekst (Aptos)' ] + $ty( 'typography', 'aptos', 400 ),
		[ '_id' => 'accent', 'title' => 'Accent (Patrick Hand)' ] + $ty( 'typography', 'Patrick Hand', 400, null, null, [ 'text_transform' => 'uppercase' ] ),
	],
	'body_color' => '#46211A',
	'link_normal_color' => '#BD5C38',
	'link_hover_color' => '#963322',
	'container_width' => $s( 1140 ),
	'container_width_tablet' => $s( 1024 ),
	'container_width_mobile' => $s( 767 ),
	'space_between_widgets' => [ 'column' => '20', 'row' => '20', 'isLinked' => true, 'unit' => 'px', 'size' => 20 ],
	'page_title_selector' => 'h1.entry-title',
	'image_border_radius' => $d( 20 ),
	'button_text_color' => '#F5EDE3',
	'button_background_color' => '#BD5C38',
	'button_hover_text_color' => '#F5EDE3',
	'button_hover_background_color' => '#963322',
	'button_border_radius' => $d( 4 ),
	'button_padding' => $d( 12, 28, 12, 28 ),
	'button_hover_box_shadow_box_shadow_type' => 'yes',
	'button_hover_box_shadow_box_shadow' => [ 'horizontal' => 0, 'vertical' => 4, 'blur' => 12, 'spread' => 0, 'color' => 'rgba(70,33,26,0.25)' ],
	'form_label_color' => '#46211A',
	'form_field_text_color' => '#46211A',
	'form_field_background_color' => '#FFFFFF',
	'form_field_border_border' => 'solid',
	'form_field_border_width' => $d( 1 ),
	'form_field_border_color' => '#ECC0AE',
	'form_field_border_radius' => $d( 12 ),
	'form_field_padding' => $d( 12, 16, 12, 16 ),
	'form_field_focus_border_color' => '#BD5C38',
	'site_name' => 'Stichting Sampark',
	'site_description' => 'Biedt kinderen een toekomst',
	'hello_header_logo_type' => 'logo',
	'hello_header_menu_layout' => 'horizontal',
	'hello_footer_copyright_text' => '© Stichting Sampark · KvK 08169359 · RSIN 818925887',
] + $ty( 'body_typography', 'aptos', 400, [ 17, 17, 16 ], 1.65 )
  + $ty( 'button_typography', 'Patrick Hand', 400, [ 17, 17, 16 ], null, [ 'text_transform' => 'uppercase' ] )
  + $ty( 'form_label_typography', 'aptos', 600, [ 14, 14, 14 ] )
  + $ty( 'form_field_typography', 'aptos', 400 );

foreach ( [ 'h1' => [ 56, 46, 38, 1.15 ], 'h2' => [ 42, 36, 32, 1.2 ], 'h3' => [ 30, 28, 26, 1.25 ],
			'h4' => [ 24, 22, 21, 1.3 ], 'h5' => [ 20, 19, 18, 1.35 ], 'h6' => [ 17, 17, 16, 1.4 ] ] as $h => $v ) {
	$kit[ "{$h}_color" ] = '#46211A';
	$kit += $ty( "{$h}_typography", 'Spectral', 500, array_slice( $v, 0, 3 ), $v[3] );
}

if ( $kit_id ) {
	$current = get_post_meta( $kit_id, '_elementor_page_settings', true ) ?: [];
	update_post_meta( $kit_id, '_elementor_page_settings', array_merge( $current, $kit ) );
	WP_CLI::log( "  Elementor-kit $kit_id bijgewerkt" );
}

if ( ! empty( $media['logo_sampark'] ) ) {
	set_theme_mod( 'custom_logo', $media['logo_sampark'] );
	update_option( 'site_icon', $media['logo_sampark'] );
}

} // huisstijl

// ------------------------------------------------------------------ pagina's

$fill = function ( string $json ) use ( $media ) {
	// Super Forms-formulier op een gewone pagina (ID uit superforms-import.php)
	$forms = get_option( 'sampark_forms', [] );
	$json  = preg_replace_callback( '/\{\{form:([a-z_]+)\}\}/', fn( $m ) => (string) (int) ( $forms[ $m[1] ] ?? 0 ), $json );
	// pagina-ID's op slug, bv. om de winkelpagina's uit de sitemap te laten
	// (als JSON-lijst, zoals het Search & Select-veld van Elementor het bewaart)
	$json  = preg_replace_callback( '/"\{\{pageids:([a-z0-9,-]+)\}\}"/', fn( $m ) => wp_json_encode( array_values( array_filter( array_map(
		fn( $slug ) => (string) ( get_page_by_path( $slug )->ID ?? '' ), explode( ',', $m[1] ) ) ) ) ), $json );
	$json = preg_replace_callback( '/"\{\{imgid:([a-z0-9_]+)\}\}"/', fn( $m ) => (string) (int) ( $media[ $m[1] ] ?? 0 ), $json );
	$json = preg_replace_callback( '/\{\{img:([a-z0-9_]+)\}\}/', function ( $m ) use ( $media ) {
		$url = empty( $media[ $m[1] ] ) ? '' : wp_get_attachment_url( $media[ $m[1] ] );
		return $url ? str_replace( '/', '\/', $url ) : '';
	}, $json );
	return $json;
};

// Met JetEngine actief: statische voorbeeldblokken vervangen door echte Listing Grids en de kaart
// door een JetEngine Map Listing. Zonder JetEngine blijven de statische blokken staan.
$jet = function_exists( 'jet_engine' ) ? get_option( 'sampark_jet', [] ) : [];
$jetify = function ( array $elements ) use ( &$jetify, $jet ) {
	foreach ( $elements as $i => $el ) {
		$spec = $el['settings']['_sp_jet'] ?? null;
		if ( $spec && 'archive' === $spec['query'] && ! empty( $jet['listings'][ $spec['listing'] ] ) ) {
			// Archief: de Listing Grid toont de berichten van het archief zelf, met "Meer nieuws" (Load more)
			$cols = (int) $spec['cols'];
			$elements[ $i ] = [
				'id' => $el['id'], 'elType' => 'widget', 'widgetType' => 'jet-listing-grid', 'elements' => [],
				'settings' => [
					'_title' => $el['settings']['_title'] ?? 'Listing Grid',
					'lisitng_id' => (string) $jet['listings'][ $spec['listing'] ],
					'columns' => (string) $cols, 'columns_tablet' => (string) min( 2, $cols ), 'columns_mobile' => '1',
					'is_archive_template' => 'yes', 'posts_num' => 9, 'equal_columns_height' => 'yes',
					'use_load_more' => 'yes', 'load_more_type' => 'click', 'load_more_id' => 'sp-meer-nieuws',
					'horizontal_gap' => [ 'unit' => 'px', 'size' => 24 ], 'vertical_gap' => [ 'unit' => 'px', 'size' => 24 ],
					'not_found_message' => 'Nog geen berichten in deze categorie.',
				],
			];
			continue;
		}
		if ( $spec && ! empty( $jet['listings'][ $spec['listing'] ] ) && ! empty( $jet['queries'][ $spec['query'] ] ) ) {
			$cols = (int) $spec['cols'];
			$elements[ $i ] = [
				'id' => $el['id'], 'elType' => 'widget', 'widgetType' => 'jet-listing-grid', 'elements' => [],
				'settings' => [
					'_title' => $el['settings']['_title'] ?? 'Listing Grid',
					'lisitng_id' => (string) $jet['listings'][ $spec['listing'] ],
					'columns' => (string) $cols, 'columns_tablet' => (string) min( 2, $cols ), 'columns_mobile' => '1',
					'custom_query' => 'yes', 'custom_query_id' => (string) $jet['queries'][ $spec['query'] ],
					'posts_num' => 12, 'equal_columns_height' => 'yes',
					'horizontal_gap' => [ 'unit' => 'px', 'size' => 24 ], 'vertical_gap' => [ 'unit' => 'px', 'size' => 24 ],
					'not_found_message' => 'Hier staat nu niets.',
					'hide_widget_if' => empty( $spec['hide_empty'] ) ? '' : 'empty_query',
				],
			];
			continue;
		}
		// Kaart: standaard alle scholen en opleidingen (q_kaart); een andere query en zoom kunnen in de titel staan
		$map_title = $el['settings']['_title'] ?? '';
		$map_query = preg_match( '/· (q_[a-z_]+)/', $map_title, $mq ) ? $mq[1] : 'q_kaart';
		if ( 'html' === ( $el['widgetType'] ?? '' ) && str_starts_with( $map_title, 'KAART' )
			&& ! empty( $jet['listings']['kaartpopup'] ) && ! empty( $jet['queries'][ $map_query ] ) ) {
			$h = preg_match( '/sp-map__canvas" style="min-height:(\d+)px/', $el['settings']['html'], $mm ) ? (int) $mm[1] : 520;
			$zoom = preg_match( '/zoom (\d+)/', $map_title, $mz ) ? (int) $mz[1] : 12;
			$elements[ $i ] = [
				'id' => $el['id'], 'elType' => 'widget', 'widgetType' => 'jet-engine-maps-listing', 'elements' => [],
				'settings' => [
					'_title' => 'Kaart · JetEngine Map Listing (projecten met Map-veld locatie)',
					'lisitng_id' => (string) $jet['listings']['kaartpopup'],
					'custom_query' => 'yes', 'custom_query_id' => (string) $jet['queries'][ $map_query ],
					'address_field' => 'locatie', 'posts_num' => 50,
					'map_height' => [ 'unit' => 'px', 'size' => $h ], 'auto_center' => 'yes', 'max_zoom' => $zoom, 'min_zoom' => 4,
					'marker_clustering' => 'yes', 'cluster_radius' => 60,
					'marker_type' => 'icon', 'marker_icon' => [ 'value' => 'fas fa-map-marker-alt', 'library' => 'fa-solid' ],
					'marker_icon_size' => [ 'unit' => 'px', 'size' => 34 ], 'marker_icon_color' => '#963322',
					'marker_bg_color' => 'rgba(0,0,0,0)', 'marker_color' => '#963322',
					'popup_width' => 260, 'popup_pin_color' => '#ffffff',
				],
			];
			continue;
		}
		if ( ! empty( $el['elements'] ) ) {
			$elements[ $i ]['elements'] = $jetify( $el['elements'] );
		}
	}
	return $elements;
};

if ( ! $only_templates ) {
$files = glob( SP_PAGES . '*.json' );
usort( $files, fn( $a, $b ) => ( json_decode( file_get_contents( $a ), true )['menu_order'] ?? 0 ) <=> ( json_decode( file_get_contents( $b ), true )['menu_order'] ?? 0 ) );

foreach ( $files as $file ) {
	$doc = json_decode( file_get_contents( $file ), true );
	$parent = 0;
	if ( ! empty( $doc['parent'] ) ) {
		$p = get_page_by_path( $doc['parent'] );
		$parent = $p ? $p->ID : 0;
	}
	$path = ( $doc['parent'] ? $doc['parent'] . '/' : '' ) . $doc['slug'];
	$existing = get_page_by_path( $path );
	$postarr = [
		'post_type' => 'page', 'post_status' => 'publish', 'post_title' => $doc['title'],
		'post_name' => $doc['slug'], 'post_parent' => $parent, 'menu_order' => $doc['menu_order'],
		'post_content' => '',
	];
	if ( $existing ) {
		$postarr['ID'] = $existing->ID;
	}
	$id = wp_insert_post( $postarr, true );
	if ( is_wp_error( $id ) ) {
		WP_CLI::warning( "Pagina {$doc['slug']}: " . $id->get_error_message() );
		continue;
	}
	$data = $fill( wp_json_encode( $jet ? $jetify( $doc['content'] ) : $doc['content'], JSON_UNESCAPED_UNICODE ) );
	update_post_meta( $id, '_elementor_data', wp_slash( $data ) );
	update_post_meta( $id, '_elementor_edit_mode', 'builder' );
	update_post_meta( $id, '_elementor_template_type', 'wp-page' );
	update_post_meta( $id, '_elementor_page_settings', $doc['page_settings'] ?? [] );
	update_post_meta( $id, '_wp_page_template', $doc['template'] ?? 'elementor_header_footer' );
	if ( defined( 'ELEMENTOR_VERSION' ) ) {
		update_post_meta( $id, '_elementor_version', ELEMENTOR_VERSION );
	}
	if ( ! empty( $doc['seo'] ) ) {
		update_post_meta( $id, '_yoast_wpseo_title', $doc['seo'][0] );
		update_post_meta( $id, '_yoast_wpseo_metadesc', $doc['seo'][1] );
	}
	WP_CLI::log( sprintf( '  %s /%s/ (%d)', $existing ? '~' : '+', $path, $id ) );
}

// Losse schoolpagina's van eerdere builds opruimen: /ons-werk/{school}/ is nu de projectsingle
// (Theme Builder-template "Single · Project"). Alleen pagina's met dezelfde slug als een project.
$ons_werk = get_page_by_path( 'ons-werk' );
if ( $jet && $ons_werk && post_type_exists( 'projecten' ) && defined( 'ELEMENTOR_PRO_VERSION' ) ) {
	foreach ( get_pages( [ 'parent' => $ons_werk->ID, 'post_status' => 'publish,draft' ] ) as $old ) {
		if ( get_page_by_path( $old->post_name, OBJECT, 'projecten' ) ) {
			wp_trash_post( $old->ID );
			WP_CLI::log( "  - /ons-werk/{$old->post_name}/ (pagina naar prullenbak, nu projectsingle)" );
		}
	}
}

// Productbeelden (alleen als een product nog geen beeld heeft)
$product_images = [ 'donatie' => 'steun_doneer', 'sponsor-een-kind' => 'steun_kind', 'peetal-brons' => 'steun_bedrijf',
	'chandee-zilver' => 'steun_bedrijf', 'sona-goud' => 'steun_bedrijf', 'rode-wijn' => 'event_wijn',
	'witte-wijn' => 'event_wijn', 'alcoholvrij' => 'event_wijn', 'ticket-sampark-rally' => 'event_rally',
	'golftoernooi' => 'event_golf' ];
foreach ( get_posts( [ 'post_type' => 'product', 'post_status' => 'any', 'numberposts' => -1 ] ) as $product ) {
	$key = $product_images[ $product->post_name ] ?? ( 'Alcoholvrij mousserend' === $product->post_title ? 'event_wijn' : '' );
	if ( $key && ! empty( $media[ $key ] ) && ! has_post_thumbnail( $product ) ) {
		set_post_thumbnail( $product, $media[ $key ] );
	}
}

} // pagina's

// ------------------------------------------------------------------ Theme Builder-templates (Elementor Pro)

if ( defined( 'ELEMENTOR_PRO_VERSION' ) ) {
	$forms = get_option( 'sampark_forms', [] );
	foreach ( glob( '/elementor/templates/*.json' ) as $file ) {
		$doc = json_decode( file_get_contents( $file ), true );
		// De singles draaien op JetEngine-velden en de productvarianten op Super Forms: zonder die plugins overslaan
		if ( str_starts_with( $doc['key'], 'single-' ) && ! $jet ) {
			continue;
		}
		$json = wp_json_encode( [ $doc['content'], $doc['conditions'] ], JSON_UNESCAPED_UNICODE );
		$missing = false;
		$json = preg_replace_callback( '/\{\{(form|pcat|glossary):([a-z0-9_-]+)\}\}/', function ( $m ) use ( $forms, $jet, &$missing ) {
			$val = match ( $m[1] ) {
				'form'     => $forms[ $m[2] ] ?? 0,
				'pcat'     => get_term_by( 'slug', $m[2], 'product_cat' )->term_id ?? 0,
				'glossary' => $jet['glossary'][ $m[2] ] ?? 0,
			};
			$missing = $missing || ! $val;
			return (string) $val;
		}, $json );
		if ( $missing ) {
			WP_CLI::log( "  - template {$doc['title']} overgeslagen (formulier, categorie of glossary ontbreekt)" );
			continue;
		}
		[ $doc['content'], $doc['conditions'] ] = json_decode( $json, true );
		$existing = get_posts( [ 'post_type' => 'elementor_library', 'post_status' => 'any', 'numberposts' => 1, 'fields' => 'ids',
			'meta_key' => '_sampark_key', 'meta_value' => $doc['key'] ] );
		if ( $existing && $only_templates ) {
			continue; // bestaat al en kan met de hand zijn aangepast
		}
		$tid = $existing ? $existing[0] : wp_insert_post( [ 'post_type' => 'elementor_library', 'post_status' => 'publish',
			'post_title' => $doc['title'] ] );
		if ( ! $tid || is_wp_error( $tid ) ) {
			WP_CLI::warning( "Template {$doc['key']} niet aangemaakt" );
			continue;
		}
		$content = $jet ? $jetify( $doc['content'] ) : $doc['content'];
		update_post_meta( $tid, '_sampark_key', $doc['key'] );
		update_post_meta( $tid, '_elementor_template_type', $doc['type'] );
		update_post_meta( $tid, '_elementor_edit_mode', 'builder' );
		update_post_meta( $tid, '_elementor_data', wp_slash( $fill( wp_json_encode( $content, JSON_UNESCAPED_UNICODE ) ) ) );
		update_post_meta( $tid, '_elementor_page_settings', $doc['page_settings'] ?: [] );
		update_post_meta( $tid, '_elementor_conditions', $doc['conditions'] );
		update_post_meta( $tid, '_elementor_version', ELEMENTOR_VERSION );
		update_post_meta( $tid, '_elementor_pro_version', ELEMENTOR_PRO_VERSION );
		wp_set_object_terms( $tid, $doc['type'], 'elementor_library_type' );
		WP_CLI::log( sprintf( '  %s template %s (%d)', $existing ? '~' : '+', $doc['title'], $tid ) );
	}
	\ElementorPro\Modules\ThemeBuilder\Module::instance()->get_conditions_manager()->get_cache()->regenerate();
}

if ( class_exists( '\Elementor\Plugin' ) ) {
	\Elementor\Plugin::$instance->files_manager->clear_cache();
}
