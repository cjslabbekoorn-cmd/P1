<?php
/**
 * Plugin Name: Sampark preview singles
 * Description: Tijdelijk, tot de Theme Builder-templates (Elementor Pro) er zijn: als er onder /ons-werk/
 *              een gebouwde pagina bestaat met dezelfde slug als een project, toont WordPress die pagina
 *              in plaats van de kale projectsingle. Verwijderen zodra de Single-template voor projecten staat.
 */

add_filter( 'request', function ( $vars ) {
	if ( defined( 'ELEMENTOR_PRO_VERSION' ) || empty( $vars['projecten'] ) || ! empty( $vars['preview'] ) ) {
		return $vars;
	}
	$path = 'ons-werk/' . sanitize_title( $vars['projecten'] );
	if ( get_page_by_path( $path ) ) {
		return [ 'pagename' => $path ];
	}
	return $vars;
} );
