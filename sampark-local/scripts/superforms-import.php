<?php
/**
 * Importeert de vier Super Forms-formulieren die op staging in gebruik zijn (superforms/forms.json,
 * gehaald uit de WordPress-export van 27-10-2026; de 100 automatische back-ups zijn weggelaten).
 * Draait via setup.sh:  wp eval-file /scripts/superforms-import.php
 * Bewaart de lokale ID's in de optie sampark_forms (wijn, rally, golf, donatie).
 */

if ( ! post_type_exists( 'super_form' ) ) {
	WP_CLI::warning( 'Super Forms is niet actief; formulieren overgeslagen.' );
	return;
}

$forms = json_decode( file_get_contents( '/superforms/forms.json' ), true );
$map   = get_option( 'sampark_forms', [] );

foreach ( $forms as $form ) {
	$id = (int) ( $map[ $form['key'] ] ?? 0 );
	if ( $id && get_post( $id ) ) {
		continue;
	}
	$id = wp_insert_post( [ 'post_type' => 'super_form', 'post_status' => 'publish', 'post_title' => $form['title'] ], true );
	if ( is_wp_error( $id ) ) {
		WP_CLI::warning( $form['title'] . ': ' . $id->get_error_message() );
		continue;
	}
	foreach ( $form['meta'] as $key => $value ) {
		// waarden staan geserialiseerd in de export; zo terugzetten als WordPress ze bewaarde
		update_post_meta( $id, $key, maybe_unserialize( $value ) );
	}
	$map[ $form['key'] ] = $id;
	WP_CLI::log( "  + formulier {$form['title']} ($id, op staging {$form['staging_id']})" );
}
// Donatieformulier voor de doneerpagina: hetzelfde formulier, maar met het product "Eenmalige donatie" vast ingevuld.
// Het origineel vult product_id met {post_id}; dat werkt alleen op de productpagina zelf.
$product = get_page_by_path( 'donatie', OBJECT, 'product' );
if ( $product && ! empty( $map['donatie'] ) && ( empty( $map['donatie_pagina'] ) || ! get_post( $map['donatie_pagina'] ) ) ) {
	$fix = function ( $items ) use ( &$fix, $product ) {
		foreach ( $items as $k => $item ) {
			if ( is_array( $item ) ) {
				if ( 'product_id' === ( $item['data']['name'] ?? '' ) ) {
					$item['data']['value'] = (string) $product->ID;
				}
				$items[ $k ] = $fix( $item );
			}
		}
		return $items;
	};
	$id = wp_insert_post( [ 'post_type' => 'super_form', 'post_status' => 'publish', 'post_title' => 'Donatieformulier (doneerpagina)' ] );
	foreach ( get_post_meta( $map['donatie'] ) as $key => $values ) {
		$value = maybe_unserialize( $values[0] );
		update_post_meta( $id, $key, '_super_elements' === $key && is_array( $value ) ? $fix( $value ) : $value );
	}
	$map['donatie_pagina'] = $id;
	WP_CLI::log( "  + formulier Donatieformulier (doneerpagina) ($id, product {$product->ID})" );
}
update_option( 'sampark_forms', $map, false );
