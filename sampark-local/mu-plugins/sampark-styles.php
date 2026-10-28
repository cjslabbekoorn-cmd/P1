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
/* JetEngine Listing Grid: kaarten even hoog, knop onderaan */
.jet-listing-grid__item > .jet-engine-listing-overlay-wrap,
.jet-listing-grid__item > .jet-engine-listing-overlay-wrap > .elementor,
.jet-listing-grid__item > .jet-engine-listing-overlay-wrap > .elementor > .e-con { height: 100%; }
.sp-card > .elementor-widget-jet-listing-dynamic-link:last-child { margin-top: auto; }
/* JetEngine Map Listing in huisstijl */
.jet-map-listing { border-radius: 20px; overflow: hidden; }
.jet-map-listing .leaflet-tile-pane { filter: sepia(.35) saturate(.75) brightness(1.03); }
.jet-map-listing .leaflet-popup-content-wrapper { border-radius: 16px; }
.jet-map-listing .jet-map-marker { color: #963322; }
.jet-map-listing .marker-cluster { background: rgba(150, 51, 34, .25) !important; }
.jet-map-listing .marker-cluster div { background: #963322 !important; color: #F5EDE3 !important;
	font-family: "Patrick Hand", sans-serif; font-size: 16px; }
/* Statuschip in event-kaarten */
.sp-chip { display: inline-block; padding: 4px 12px; border-radius: 999px; background: #ECC0AE; color: #963322;
	font-family: "Patrick Hand", sans-serif; text-transform: uppercase; font-size: 15px; letter-spacing: .3px; }
/* Footer: logo in crème op donker */
.sp-logo-light img { filter: brightness(0) invert(.94); }
.elementor-location-footer .jet-listing-dynamic-field__content p { margin: 0; }
/* Topbalk: tekst op één regel */
.elementor-location-header .elementor-widget-text-editor p { white-space: nowrap; margin: 0; }
@media (max-width: 767px) { .elementor-location-header .elementor-button { padding: 10px 16px; } }
/* Topbalk-links zonder schaduw van de kit-knoppen */
.elementor-location-header .elementor-button:hover { box-shadow: none; }
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
/* Singles: sectie met een lege Listing Grid verbergen (de grid zelf staat op "Hide widget if: Query is empty") */
.sp-hide-empty:not(:has(.jet-listing-grid__item, .sp-keep)) { display: none; }
/* Single project: feiten, voorzieningen, momenten. JetEngine zet elk repeater-item op flex; onze blokken niet */
.sp-facts .jet-listing-dynamic-repeater__item > .sp-fact, .sp-moments .jet-listing-dynamic-repeater__item > .sp-moment { display: block; }
.sp-programma .jet-listing-dynamic-repeater__item > .sp-prog { display: grid; }
.sp-facts .jet-listing-dynamic-repeater__item, .sp-moments .jet-listing-dynamic-repeater__item { display: block; }
.sp-facts .jet-listing-dynamic-repeater__items { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.sp-fact { text-align: center; }
.sp-fact strong { display: block; font-family: Spectral, serif; font-weight: 500; font-size: 46px; line-height: 1.1; color: #963322; }
.sp-checks .jet-listing-dynamic-repeater__items { display: flex; flex-direction: column; gap: 8px; }
.sp-check::before { content: "✓"; color: #ED7404; font-weight: 700; margin-right: 10px; }
.sp-moments .jet-listing-dynamic-repeater__items { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.sp-moment { background: #F5EDE3; border-radius: 20px; padding: 28px; height: 100%; }
.sp-moment__when { font-family: "Patrick Hand", sans-serif; text-transform: uppercase; font-size: 20px; color: #ED7404; }
.sp-moment p { margin: 8px 0 0; }
.sp-checklist .jet-check-list__item { background: #FFFFFF; border-radius: 16px; padding: 18px 20px; font-size: 18px; }
.sp-checklist .jet-check-list__item-icon { color: #ED7404; }
/* Single evenement: praktische info en programma */
.sp-info { background: #F5EDE3; border-radius: 20px; padding: 22px; }
.sp-info p { margin: 0; }
.sp-programma .jet-listing-dynamic-repeater__items { display: flex; flex-direction: column; }
.sp-prog { display: grid; grid-template-columns: 120px 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(70, 33, 26, .15); }
.sp-prog span { font-family: "Patrick Hand", sans-serif; font-size: 18px; color: #ED7404; }
/* Product: Super Forms-formulier in de kolom */
.sp-product .super-form { margin-top: 8px; }
@media (max-width: 767px) {
	.sp-facts .jet-listing-dynamic-repeater__items { grid-template-columns: repeat(2, 1fr); }
	.sp-fact strong { font-size: 34px; }
	.sp-moments .jet-listing-dynamic-repeater__items { grid-template-columns: 1fr; }
}
/* Nieuwsberichten: fotoseries als grid, alle foto's even groot; klik opent de Elementor-lightbox */
.sp-gallery { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 24px 0; }
.sp-gallery a, .sp-gallery img { display: block; }
.sp-gallery > br, .sp-gallery > p:empty { display: none; }
.sp-gallery img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border-radius: 12px; }
.elementor-widget-theme-post-content img { border-radius: 12px; height: auto; }
@media (max-width: 767px) { .sp-gallery { grid-template-columns: repeat(2, 1fr); } }
/* Nieuwsarchief: categorieknoppen compact */
.sp-cats .elementor-button { padding: 8px 16px; font-size: 15px; }
/* Product: hoge flesfoto's niet langer dan het scherm */
.elementor-widget-woocommerce-product-images .woocommerce-product-gallery__image img { max-height: 620px; object-fit: contain; }
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
