<?php
/**
 * Plugin Name: Sampark styles
 * Description: Kleine aanvullingen op de Elementor-kit (sampark-styles.css). Op staging en live staan ze in
 *              Elementor > Site-instellingen > Aangepaste CSS (scripts/staging-klaar.php zet ze daar);
 *              dan laadt deze plugin ze niet nog een keer.
 */

/** Staat de CSS al in de Elementor-kit? Dan niet dubbel laden. */
function sampark_styles_in_kit() {
	$kit = (int) get_option( 'elementor_active_kit' );
	$set = $kit ? get_post_meta( $kit, '_elementor_page_settings', true ) : [];
	return is_array( $set ) && str_contains( (string) ( $set['custom_css'] ?? '' ), '/* sampark-styles' );
}

add_action( 'wp_enqueue_scripts', function () {
	$css = sampark_styles_in_kit() ? '' : (string) file_get_contents( __DIR__ . '/sampark-styles.css' );
	// Adobe Fonts (Aptos). Met Elementor Pro laadt de Adobe Fonts-integratie de kit zelf.
	$kit = get_option( 'elementor_typekit-kit-id' );
	if ( $kit && ! defined( 'ELEMENTOR_PRO_VERSION' ) ) {
		wp_enqueue_style( 'sampark-adobe-fonts', 'https://use.typekit.net/' . rawurlencode( $kit ) . '.css', [], null );
	}
	if ( $css ) {
		wp_register_style( 'sampark', false );
		wp_enqueue_style( 'sampark' );
		wp_add_inline_style( 'sampark', $css );
	}
}, 20 );
