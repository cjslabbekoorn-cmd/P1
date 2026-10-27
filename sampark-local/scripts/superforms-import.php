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
update_option( 'sampark_forms', $map, false );
