<?php
/**
 * Plugin Name: AYCL Support Zoeken
 * Description: Relevantie-zoeken voor de kennisbank (CPT support), als lichte vervanger van Relevanssi. Werkt alleen voor de Elementor-zoekwidget met Query ID "relevanssi_search" en laat alle andere zoekopdrachten op de site met rust.
 * Version: 1.0.0
 * Requires at least: 6.0
 * Requires PHP: 7.4
 * Author: Positie1
 * Text Domain: aycl-support-zoeken
 */

defined( 'ABSPATH' ) || exit;

/*
 * Werking
 * -------
 * 1. De Elementor-zoekwidget heeft Query ID "relevanssi_search". Elementor
 *    roept dan de actie elementor/query/relevanssi_search aan, zowel op de
 *    resultatenpagina als bij de live-resultaten (REST-route
 *    /elementor-pro/v1/refresh-search). Alleen daar zetten we een eigen vlag
 *    op de query. De Query ID is gelijk gehouden aan die van de oude
 *    Relevanssi-snippet, zodat er in Elementor niets hoeft te veranderen.
 * 2. Alleen queries met die vlag worden via posts_pre_query door ons
 *    beantwoord: kandidaten ophalen met één SQL-query, scoren in PHP,
 *    sorteren op relevantie en pagineren. Alle andere queries (JetSmartFilters,
 *    admin, gewone WordPress-zoekopdrachten) komen hier nooit langs.
 *
 * Relevantie (vergelijkbaar met de standaardinstellingen van Relevanssi):
 * - Eerst moeten alle zoekwoorden voorkomen (EN). Levert dat niets op, dan
 *   volstaat één zoekwoord (OF).
 * - Gewicht per treffer: titel 5, samenvatting 2, inhoud 1. Een heel woord
 *   telt zwaarder dan een deel van een woord ("inlog" vindt ook "inloggen").
 * - De hele zoekzin in de titel geeft een extra bonus.
 * - Gelijke score: nieuwste eerst.
 */

const AYCL_ZOEK_QUERY_ID  = 'relevanssi_search';
const AYCL_ZOEK_VLAG      = 'aycl_support_zoeken';
const AYCL_ZOEK_POST_TYPE = 'support';

add_action(
	'elementor/query/' . AYCL_ZOEK_QUERY_ID,
	function ( $query ) {
		$query->set( AYCL_ZOEK_VLAG, true );
		$query->set( 'post_type', AYCL_ZOEK_POST_TYPE );
	},
	1
);

add_filter(
	'posts_pre_query',
	function ( $posts, $query ) {
		if ( null !== $posts || ! $query->get( AYCL_ZOEK_VLAG ) ) {
			return $posts;
		}
		$zoekterm = trim( (string) $query->get( 's' ) );
		$termen   = aycl_zoek_termen( $zoekterm );
		if ( ! $termen ) {
			return $posts; // Lege zoekopdracht: WordPress doet het zelf.
		}
		return aycl_zoek_uitvoeren( $query, $zoekterm, $termen );
	},
	10,
	2
);

/**
 * Splitst de zoekopdracht in unieke, genormaliseerde zoekwoorden.
 *
 * @return string[]
 */
function aycl_zoek_termen( string $zoekterm ): array {
	$woorden = preg_split( '/[^\p{L}\p{N}]+/u', aycl_zoek_normaliseer( $zoekterm ), -1, PREG_SPLIT_NO_EMPTY );
	$woorden = array_filter(
		$woorden,
		function ( $w ) {
			return mb_strlen( $w ) >= 2;
		}
	);
	return array_values( array_unique( $woorden ) );
}

/**
 * Kleine letters, zonder accenten en HTML, zodat "Cursussen", "cursussen"
 * en "cursussén" gelijk zijn.
 */
function aycl_zoek_normaliseer( string $tekst ): string {
	$tekst = wp_strip_all_tags( strip_shortcodes( $tekst ) );
	$tekst = html_entity_decode( $tekst, ENT_QUOTES | ENT_HTML5, 'UTF-8' );
	return mb_strtolower( remove_accents( $tekst ), 'UTF-8' );
}

/**
 * Score van één bericht. 0 betekent: voldoet niet (in EN-modus ontbreekt
 * een zoekwoord, in OF-modus komt geen enkel zoekwoord voor).
 *
 * @param array{titel:string,samenvatting:string,inhoud:string} $velden Genormaliseerde tekst.
 * @param string[]                                              $termen
 */
function aycl_zoek_score( array $velden, array $termen, string $zin, bool $alle_termen ): float {
	$gewichten = apply_filters(
		'aycl_zoek_gewichten',
		array(
			'titel'        => 5,
			'samenvatting' => 2,
			'inhoud'       => 1,
		)
	);

	$score    = 0.0;
	$gevonden = 0;
	foreach ( $termen as $term ) {
		$term_score = 0.0;
		$heel_woord = '/(?<![\p{L}\p{N}])' . preg_quote( $term, '/' ) . '(?![\p{L}\p{N}])/u';
		foreach ( $gewichten as $veld => $gewicht ) {
			$tekst = $velden[ $veld ] ?? '';
			if ( '' === $tekst ) {
				continue;
			}
			$deel = substr_count( $tekst, $term );
			if ( ! $deel ) {
				continue;
			}
			$heel = preg_match_all( $heel_woord, $tekst );
			// Hele woorden tellen dubbel; aantal treffers dempen zodat een lange
			// tekst niet wint van een korte, gerichte titel.
			$term_score += $gewicht * ( 1 + log( 1 + $deel + $heel ) );
		}
		if ( $term_score > 0 ) {
			++$gevonden;
			$score += $term_score;
		} elseif ( $alle_termen ) {
			return 0.0;
		}
	}
	if ( ! $gevonden ) {
		return 0.0;
	}
	if ( count( $termen ) > 1 && '' !== $zin && false !== strpos( $velden['titel'], $zin ) ) {
		$score += 10;
	}
	return $score;
}

/**
 * Voert de zoekopdracht uit en vult found_posts/max_num_pages zelf, want
 * WordPress doet dat niet als posts_pre_query iets teruggeeft.
 *
 * @param string[] $termen
 * @return WP_Post[]|int[]
 */
function aycl_zoek_uitvoeren( WP_Query $query, string $zoekterm, array $termen ): array {
	global $wpdb;

	$post_types = (array) $query->get( 'post_type' );
	$post_types = $post_types ? $post_types : array( AYCL_ZOEK_POST_TYPE );

	// Kandidaten: minstens één zoekwoord in titel, samenvatting of inhoud.
	$of = array();
	$args = array();
	foreach ( $termen as $term ) {
		$like = '%' . $wpdb->esc_like( $term ) . '%';
		$of[] = '(post_title LIKE %s OR post_excerpt LIKE %s OR post_content LIKE %s)';
		array_push( $args, $like, $like, $like );
	}
	$types_sql = implode( ',', array_fill( 0, count( $post_types ), '%s' ) );
	$sql       = "SELECT ID, post_title, post_excerpt, post_content, post_date
		FROM {$wpdb->posts}
		WHERE post_type IN ($types_sql)
		AND post_status = 'publish'
		AND post_password = ''
		AND (" . implode( ' OR ', $of ) . ')';
	// phpcs:ignore WordPress.DB.PreparedSQL.NotPrepared -- placeholders hierboven opgebouwd.
	$rijen = $wpdb->get_results( $wpdb->prepare( $sql, array_merge( $post_types, $args ) ) );

	// LIKE is in MySQL meestal al hoofdletter- en accentongevoelig, maar de
	// score normaliseert zelf ook, zodat die niet van de collatie afhangt.
	$zin       = aycl_zoek_normaliseer( $zoekterm );
	$kandidaten = array();
	foreach ( (array) $rijen as $rij ) {
		$kandidaten[] = array(
			'id'     => (int) $rij->ID,
			'datum'  => $rij->post_date,
			'velden' => array(
				'titel'        => aycl_zoek_normaliseer( $rij->post_title ),
				'samenvatting' => aycl_zoek_normaliseer( $rij->post_excerpt ),
				'inhoud'       => aycl_zoek_normaliseer( $rij->post_content ),
			),
		);
	}

	$resultaten = aycl_zoek_rangschik( $kandidaten, $termen, $zin, true );
	if ( ! $resultaten && count( $termen ) > 1 ) {
		$resultaten = aycl_zoek_rangschik( $kandidaten, $termen, $zin, false );
	}
	$ids = array_keys( $resultaten );

	// Pagineren zoals WP_Query dat zou doen.
	$per_pagina = (int) $query->get( 'posts_per_page' );
	$per_pagina = 0 === $per_pagina ? (int) get_option( 'posts_per_page' ) : $per_pagina;
	$totaal     = count( $ids );
	if ( $per_pagina > 0 ) {
		$offset = $query->get( 'offset' );
		if ( '' === $offset || null === $offset ) {
			$pagina = max( 1, (int) $query->get( 'paged' ) );
			$offset = ( $pagina - 1 ) * $per_pagina;
		}
		$ids = array_slice( $ids, (int) $offset, $per_pagina );
	}

	$query->found_posts   = $totaal;
	$query->max_num_pages = $per_pagina > 0 ? (int) ceil( $totaal / $per_pagina ) : 1;
	$query->set( 'orderby', 'relevance' );

	if ( 'ids' === $query->get( 'fields' ) ) {
		return $ids;
	}
	if ( ! $ids ) {
		return array();
	}
	_prime_post_caches( $ids );
	return array_values( array_filter( array_map( 'get_post', $ids ) ) );
}

/**
 * @return array<int,float> post-ID => score, hoogste eerst (bij gelijke
 *                          score de nieuwste eerst).
 */
function aycl_zoek_rangschik( array $kandidaten, array $termen, string $zin, bool $alle_termen ): array {
	$scores = array();
	foreach ( $kandidaten as $k ) {
		$score = aycl_zoek_score( $k['velden'], $termen, $zin, $alle_termen );
		if ( $score > 0 ) {
			$scores[] = array( $k['id'], $score, $k['datum'] );
		}
	}
	usort(
		$scores,
		function ( $a, $b ) {
			return ( $b[1] <=> $a[1] ) ?: strcmp( $b[2], $a[2] );
		}
	);
	$uit = array();
	foreach ( $scores as $s ) {
		$uit[ $s[0] ] = $s[1];
	}
	return $uit;
}
