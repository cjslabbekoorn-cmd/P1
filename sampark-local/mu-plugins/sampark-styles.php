<?php
/**
 * Plugin Name: Sampark styles
 * Description: Kleine aanvullingen op de Elementor-kit. In productie hoort deze CSS in
 *              Elementor > Site Settings > Custom CSS (Pro); lokaal laden we hem hier.
 */

add_action( 'wp_enqueue_scripts', function () {
	$css = <<<'CSS'
/* Kaarten: knop altijd onderaan, ook bij ongelijke tekstlengte */
.sp-card > .elementor-widget-button:last-child, .sp-card > .elementor-widget-wrap > .elementor-widget-button:last-child { margin-top: auto; }
/* Statuschip in event-kaarten */
.sp-chip { display: inline-block; padding: 4px 12px; border-radius: 999px; background: #ECC0AE; color: #963322;
	font-family: "Patrick Hand", sans-serif; text-transform: uppercase; font-size: 15px; letter-spacing: .3px; }
/* Gegevenslijst ANBI */
.sp-dl { display: grid; grid-template-columns: max-content 1fr; gap: 6px 20px; margin: 0; }
.sp-dl dt { font-weight: 600; }
.sp-dl dd { margin: 0; }
/* Hello Elementor: header en footer in huisstijl (lokaal; in productie Theme Builder) */
.site-header { background: #F5EDE3; padding-block: 12px; }
.site-header .header-inner { display: flex; flex-direction: row; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
.site-header .site-logo img, .site-header .custom-logo { max-height: 56px; width: auto; }
.site-footer .site-logo img, .site-footer .custom-logo { max-height: 44px; width: auto; filter: brightness(0) invert(.96); }
.site-header .site-navigation ul.menu li a { color: #46211A; font-weight: 600; }
.site-header .site-navigation ul.menu li a:hover { color: #963322; }
.site-footer { background: #46211A; color: #F5EDE3; }
.site-footer a { color: #ECC0AE; }
CSS;
	// Adobe Fonts (Aptos). Met Elementor Pro laadt de Adobe Fonts-integratie de kit zelf.
	$kit = get_option( 'elementor_typekit-kit-id' );
	if ( $kit && ! defined( 'ELEMENTOR_PRO_VERSION' ) ) {
		wp_enqueue_style( 'sampark-adobe-fonts', 'https://use.typekit.net/' . rawurlencode( $kit ) . '.css', [], null );
	}
	wp_register_style( 'sampark', false );
	wp_enqueue_style( 'sampark' );
	wp_add_inline_style( 'sampark', $css );
}, 20 );
