<?php
/**
 * Zet de actuele inhoud van live en staging in de lokale site (uit content/live.json).
 *
 *   docker compose run --rm wpcli eval-file /scripts/content-import.php
 *
 * - 38 nieuwsberichten met volledige tekst, beelden, categorie en koppeling aan evenementen en projecten
 * - algemene voorwaarden en jaarrekening 2024 (pdf) in de mediabibliotheek, ANBI-documenten in de Options Page
 * - tijdloze teksten voor de evenementen, de wijnen van 2026 (namen, prijs, foto's) en producttekst golf en rally
 *
 * Veilig om opnieuw te draaien: wat je zelf hebt aangepast blijft staan. Er wordt alleen inhoud gevuld die nieuw is
 * of nog de voorlopige tekst uit de bouw heeft. Pagina-opmaak (Elementor) wordt niet aangeraakt, behalve de drie
 * voorbeeldkaarten bij Documenten op de ANBI-pagina.
 */

require_once ABSPATH . 'wp-admin/includes/media.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/image.php';

$data = json_decode( file_get_contents( '/content/live.json' ), true );
$gen  = json_decode( file_get_contents( '/elementor/content.json' ), true ); // de voorlopige inhoud uit de bouw
if ( ! $data || ! $gen ) {
	WP_CLI::error( 'content/live.json of elementor/content.json ontbreekt. Draai eerst: python3 content/build-live.py' );
}
const SP_PLACEHOLDER = 'Volledige tekst volgt bij de migratie van live';

// ------------------------------------------------------------------ media van live

// Elk bestand één keer: de koppeling live-URL → bijlage staat in de optie sampark_live_media.
// (wp eval-file draait dit bestand binnen een functie, dus geen globale variabele maar steeds de optie lezen.)
function sp_live_media( $url, $parent = 0, $quiet = false ) {
	$live_media = get_option( 'sampark_live_media', [] );
	if ( ! empty( $live_media[ $url ] ) && get_post( $live_media[ $url ] ) ) {
		return $live_media[ $url ];
	}
	$tmp = download_url( $url, 120 );
	if ( is_wp_error( $tmp ) ) {
		if ( ! $quiet ) {
			WP_CLI::warning( 'Niet geladen: ' . $url . ' (' . $tmp->get_error_message() . ')' );
		}
		return 0;
	}
	$id = media_handle_sideload( [ 'name' => basename( strtok( $url, '?' ) ), 'tmp_name' => $tmp ], $parent );
	if ( is_wp_error( $id ) ) {
		@unlink( $tmp );
		WP_CLI::warning( 'Niet geïmporteerd: ' . $url . ' (' . $id->get_error_message() . ')' );
		return 0;
	}
	$live_media = get_option( 'sampark_live_media', [] );
	$live_media[ $url ] = $id;
	update_option( 'sampark_live_media', $live_media, false );
	return $id;
}

// Liefst het originele bestand (live toont in fotoseries vaak alleen een miniatuur van 300 px); anders het formaat uit de tekst
function sp_live_original( $url, $parent ) {
	$orig = preg_replace( '/-\d+x\d+(\.\w+)$/', '$1', $url );
	return ( $orig !== $url ? sp_live_media( $orig, $parent, true ) : 0 ) ?: sp_live_media( $url, $parent );
}

// {{live:URL}} in tekst vervangen door het lokale bestand; beelden die niet te laden zijn, vervallen
function sp_fill_media( $html, $parent ) {
	$html = preg_replace_callback( '/<img src="\{\{live:([^}]+)\}\}"([^>]*)>/', function ( $m ) use ( $parent ) {
		$id = sp_live_original( $m[1], $parent );
		if ( ! $id ) {
			return '';
		}
		$src = wp_get_attachment_image_url( $id, 'large' ) ?: wp_get_attachment_url( $id );
		return '<img class="wp-image-' . $id . '" src="' . esc_url( $src ) . '"' . $m[2] . '>';
	}, $html );
	$html = preg_replace_callback( '/\{\{live:([^}]+)\}\}/', function ( $m ) use ( $parent ) {
		$id = sp_live_original( $m[1], $parent );
		return $id ? wp_get_attachment_url( $id ) : '#';
	}, $html );
	return preg_replace( '#<a href="\#">(.*?)</a>#s', '$1', $html ); // link naar een beeld dat niet te laden was
}

// ------------------------------------------------------------------ nieuws

$rel = [];
if ( function_exists( 'jet_engine' ) ) {
	foreach ( jet_engine()->relations->get_active_relations() as $r ) {
		$rel[ $r->get_args( 'name' ) ] = $r;
	}
}
$by_slug = function ( $type, $slug ) {
	$ids = get_posts( [ 'post_type' => $type, 'name' => $slug, 'post_status' => 'any', 'numberposts' => 1, 'fields' => 'ids' ] );
	return $ids ? (int) $ids[0] : 0;
};

$n_new = $n_upd = $n_skip = 0;
foreach ( $data['news'] as $n ) {
	$id      = $by_slug( 'post', $n['slug'] );
	$current = '';
	if ( $id ) {
		$current = get_post_field( 'post_content', $id );
		// Bijwerken mag als de tekst nog de voorlopige is, of nog precies zo is als deze import hem neerzette
		// (vingerafdruk _sampark_import). Zelf aangepaste berichten blijven staan.
		$untouched = md5( $current ) === get_post_meta( $id, '_sampark_import', true );
		if ( trim( $current ) !== '' && false === strpos( $current, SP_PLACEHOLDER ) && ! $untouched ) {
			$n_skip++;
			continue;
		}
		if ( $untouched && get_post_meta( $id, '_sampark_import_src', true ) === md5( $n['title'] . $n['excerpt'] . $n['content'] ) ) {
			$n_skip++; // al de laatste versie
			continue;
		}
	} else {
		$id = wp_insert_post( [ 'post_type' => 'post', 'post_status' => 'publish', 'post_name' => $n['slug'],
			'post_title' => $n['title'], 'post_date' => $n['date'] ], true );
		if ( is_wp_error( $id ) ) {
			WP_CLI::warning( "{$n['slug']}: " . $id->get_error_message() );
			continue;
		}
	}
	wp_update_post( [ 'ID' => $id, 'post_title' => $n['title'], 'post_date' => $n['date'], 'post_date_gmt' => get_gmt_from_date( $n['date'] ),
		'post_excerpt' => $n['excerpt'], 'post_content' => sp_fill_media( $n['content'], $id ) ] );
	update_post_meta( $id, '_sampark_import', md5( get_post_field( 'post_content', $id ) ) );
	update_post_meta( $id, '_sampark_import_src', md5( $n['title'] . $n['excerpt'] . $n['content'] ) );
	if ( $n['featured'] && ! has_post_thumbnail( $id ) ) {
		$thumb = sp_live_media( $n['featured'], $id );
		if ( $thumb ) {
			set_post_thumbnail( $id, $thumb );
		}
	}
	$cat = get_term_by( 'slug', $n['cat'], 'category' );
	if ( $cat ) {
		wp_set_post_categories( $id, [ $cat->term_id ] );
	}
	foreach ( $n['events'] as $ev ) {
		$eid = $by_slug( 'evenementen', $ev );
		if ( $eid && isset( $rel['Evenement ↔ Bericht'] ) ) {
			$rel['Evenement ↔ Bericht']->update( $eid, $id );
		}
	}
	foreach ( $n['projects'] as $pr ) {
		$pid = $by_slug( 'projecten', $pr );
		if ( $pid && isset( $rel['Project ↔ Bericht'] ) ) {
			$rel['Project ↔ Bericht']->update( $pid, $id );
		}
	}
	'' === $current ? $n_new++ : $n_upd++;
	WP_CLI::log( ( '' === $current ? '  + ' : '  ~ ' ) . "bericht {$n['title']}" );
}
WP_CLI::log( "  nieuws: $n_new nieuw, $n_upd aangevuld, $n_skip al gevuld (overgeslagen)" );

// ------------------------------------------------------------------ documenten

$docs = [];
foreach ( $data['documents'] as $d ) {
	$docs[ $d['key'] ] = sp_live_media( $d['url'] );
	if ( $docs[ $d['key'] ] ) {
		wp_update_post( [ 'ID' => $docs[ $d['key'] ], 'post_title' => $d['title'] ] );
	}
}
$voorwaarden_url = ! empty( $docs['algemene_voorwaarden'] ) ? wp_get_attachment_url( $docs['algemene_voorwaarden'] ) : '';
$jaarrekening_url = ! empty( $docs['jaarrekening_2024'] ) ? wp_get_attachment_url( $docs['jaarrekening_2024'] ) : '';

// Algemene voorwaarden: de pagina verwijst naar de pdf (alleen als de pagina nog leeg is)
$page = get_page_by_path( 'algemene-voorwaarden' );
if ( $page && $voorwaarden_url && '' === trim( $page->post_content ) ) {
	wp_update_post( [ 'ID' => $page->ID, 'post_content' =>
		'<p>Op bestellingen, inschrijvingen en donaties via deze website zijn de algemene voorwaarden van Stichting Sampark van toepassing.</p>' .
		'<p><a href="' . esc_url( $voorwaarden_url ) . '">Download de algemene voorwaarden (pdf)</a></p>' ] );
	WP_CLI::log( '  + algemene voorwaarden (pdf) gekoppeld aan /algemene-voorwaarden/' );
}

// ANBI-documenten in de Options Page "Stichting"
$opts = get_option( 'stichting', [] );
$opts = is_array( $opts ) ? $opts : [];
$rows = is_array( $opts['anbi_documenten'] ?? null ) ? $opts['anbi_documenten'] : [];
foreach ( $data['documents'] as $d ) {
	if ( empty( $d['jaar'] ) || empty( $docs[ $d['key'] ] ) ) {
		continue;
	}
	$url = wp_get_attachment_url( $docs[ $d['key'] ] );
	$have = array_filter( $rows, fn( $r ) => ( $r['jaar'] ?? '' ) === $d['jaar'] && ( $r['soort'] ?? '' ) === $d['soort'] );
	if ( ! $have ) { // per jaar en soort één document; een zelf geplaatste versie blijft staan
		$rows[ 'item-' . count( $rows ) ] = [ 'jaar' => $d['jaar'], 'soort' => $d['soort'], 'bestand' => $url ];
	}
}
$opts['anbi_documenten'] = $rows;
update_option( 'stichting', $opts );

// ANBI-pagina: de drie voorbeeldkaarten bij Documenten vervangen door de jaarrekening die er echt is
$anbi = get_page_by_path( 'over-ons/anbi' );
if ( $anbi && $jaarrekening_url ) {
	$el = json_decode( get_post_meta( $anbi->ID, '_elementor_data', true ), true );
	$changed = false;
	$walk = function ( array $items ) use ( &$walk, &$changed, $jaarrekening_url ) {
		$out = [];
		foreach ( $items as $item ) {
			$title = $item['settings']['_title'] ?? '';
			if ( in_array( $title, [ 'Document · 2023', 'Document · 2022' ], true ) ) {
				$changed = true; // bestaat niet op live
				continue;
			}
			if ( 'Document · 2024' === $title ) {
				foreach ( $item['elements'] as $i => $w ) {
					if ( 'button' === ( $w['widgetType'] ?? '' ) && '#' === ( $w['settings']['link']['url'] ?? '' ) ) {
						$item['elements'][ $i ]['settings']['link'] = [ 'url' => $jaarrekening_url, 'is_external' => 'on', 'nofollow' => '' ];
						$changed = true;
					}
				}
			}
			if ( ! empty( $item['elements'] ) ) {
				$item['elements'] = $walk( $item['elements'] );
			}
			$out[] = $item;
		}
		return $out;
	};
	if ( is_array( $el ) ) {
		$el = $walk( $el );
		if ( $changed ) {
			update_post_meta( $anbi->ID, '_elementor_data', wp_slash( wp_json_encode( $el, JSON_UNESCAPED_UNICODE ) ) );
			WP_CLI::log( '  + ANBI-pagina: jaarrekening 2024 gekoppeld, voorbeeldkaarten 2023 en 2022 verwijderd' );
		}
	}
}

// ------------------------------------------------------------------ evenementen

$gen_events = array_column( $gen['events'], null, 'slug' );
foreach ( $data['events'] as $slug => $e ) {
	$id = $by_slug( 'evenementen', $slug );
	if ( ! $id ) {
		continue;
	}
	$orig = $gen_events[ $slug ] ?? [];
	$upd  = [ 'ID' => $id ];
	if ( trim( get_post_field( 'post_content', $id ) ) === trim( $orig['content'] ?? '' ) ) {
		$upd['post_content'] = $e['content'];
	}
	if ( ! empty( $e['excerpt'] ) && trim( get_post_field( 'post_excerpt', $id ) ) === trim( $orig['excerpt'] ?? '' ) ) {
		$upd['post_excerpt'] = $e['excerpt'];
	}
	if ( count( $upd ) > 1 ) {
		wp_update_post( $upd );
	}
	// beeld van het bijbehorende nieuwsbericht, zolang het evenement nog het voorlopige beeld uit de bouw heeft
	if ( ! empty( $e['thumb'] ) ) {
		$gen_media = get_option( 'sampark_media', [] );
		$news_id   = $by_slug( 'post', $e['thumb'] );
		$thumb     = $news_id ? get_post_thumbnail_id( $news_id ) : 0;
		if ( $thumb && (int) get_post_thumbnail_id( $id ) === (int) ( $gen_media[ $orig['thumb'] ?? '' ] ?? -1 ) ) {
			set_post_thumbnail( $id, $thumb );
		}
	}
	foreach ( $e['meta'] ?? [] as $k => $v ) {
		$cur = get_post_meta( $id, $k, true );
		$was = $orig['meta'][ $k ] ?? '';
		if ( 'programma' === $k && is_array( $was ) ) { // JetEngine bewaart repeaters als item-0, item-1, …
			$was = array_combine( array_map( fn( $i ) => 'item-' . $i, array_keys( $was ) ), $was );
			$v   = array_combine( array_map( fn( $i ) => 'item-' . $i, array_keys( $v ) ), $v );
		}
		if ( '' === $cur || $cur == $was || ( is_array( $cur ) && array_values( $cur ) == array_values( (array) $was ) ) ) {
			update_post_meta( $id, $k, $v );
		}
	}
	WP_CLI::log( "  ~ evenement $slug" );
}

// ------------------------------------------------------------------ producten

$generic_titles = [ 'Rode wijn', 'Witte wijn', 'Alcoholvrij mousserend' ];
foreach ( $data['products'] as $old_slug => $p ) {
	$id = $by_slug( 'product', $old_slug ) ?: ( ! empty( $p['slug'] ) ? $by_slug( 'product', $p['slug'] ) : 0 );
	if ( ! $id && 'alcoholvrij' === $old_slug ) { // concept zonder slug
		$found = get_posts( [ 'post_type' => 'product', 'post_status' => 'any', 'title' => 'Alcoholvrij mousserend', 'numberposts' => 1, 'fields' => 'ids' ] );
		$id = $found ? (int) $found[0] : 0;
	}
	$product = $id ? wc_get_product( $id ) : null;
	if ( ! $product ) {
		continue;
	}
	if ( ! empty( $p['title'] ) && ( in_array( $product->get_name(), $generic_titles, true ) || $product->get_slug() === $old_slug ) ) {
		// wijn van 2026: naam, slug, prijs, teksten en foto van live
		$product->set_name( $p['title'] );
		$product->set_slug( $p['slug'] );
		$product->set_regular_price( (string) $p['price'] );
		$product->set_short_description( $p['short'] );
		$product->set_description( $p['content'] );
		$product->set_status( $p['status'] );
		if ( ! empty( $p['image'] ) ) {
			$img = sp_live_media( $p['image'], $id );
			if ( $img ) {
				$product->set_image_id( $img );
			}
		}
		$product->save();
		WP_CLI::log( "  ~ product {$p['title']} (/product/{$p['slug']}/, € {$p['price']})" );
	} elseif ( empty( $p['title'] ) && '' === trim( $product->get_description() ) ) {
		$product->set_description( $p['content'] );
		$product->save();
		WP_CLI::log( "  ~ producttekst {$product->get_name()}" );
	}
}

if ( class_exists( '\Elementor\Plugin' ) ) {
	\Elementor\Plugin::$instance->files_manager->clear_cache();
}
WP_CLI::success( 'Inhoud van live en staging staat erin.' );
