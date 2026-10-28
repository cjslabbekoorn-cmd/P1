<?php
/**
 * Winkelinstellingen zoals op staging. Herhaalbaar; draait via setup.sh en rebuild.sh.
 *   docker compose run --rm wpcli eval-file /scripts/shop-settings.php
 *
 * - geen kortingscodes (Sampark gebruikt ze niet; scheelt een veld in winkelwagen en afrekenen)
 * - verzendzone Nederland met "Gratis verzending" en "Lokaal afhalen" (wijnactie: bezorgen of afhalen in Genemuiden)
 * - wijnen zijn fysieke producten, zodat de bezorgkeuze verschijnt; tickets, donaties en pakketten blijven virtueel
 */

update_option( 'woocommerce_enable_coupons', 'no' );

$zone_id = 0;
foreach ( WC_Shipping_Zones::get_zones() as $z ) {
	if ( 'Nederland' === $z['zone_name'] ) {
		$zone_id = $z['id'];
	}
}
$zone = new WC_Shipping_Zone( $zone_id ?: null );
if ( ! $zone_id ) {
	$zone->set_zone_name( 'Nederland' );
	$zone->add_location( 'NL', 'country' );
	$zone->save();
	WP_CLI::log( '  + verzendzone Nederland' );
}
$have = array_map( fn( $m ) => $m->id, $zone->get_shipping_methods() );
foreach ( [ 'free_shipping' => 'Gratis verzending', 'local_pickup' => 'Lokaal afhalen' ] as $method => $title ) {
	if ( in_array( $method, $have, true ) ) {
		continue;
	}
	$instance = $zone->add_shipping_method( $method );
	update_option( "woocommerce_{$method}_{$instance}_settings", [ 'title' => $title, 'enabled' => 'yes' ] + ( 'local_pickup' === $method ? [ 'cost' => '' ] : [ 'requires' => '' ] ) );
	WP_CLI::log( "  + verzendmethode $title" );
}

$wine = get_term_by( 'slug', 'wijnactie', 'product_cat' );
if ( $wine ) {
	foreach ( wc_get_products( [ 'category' => [ 'wijnactie' ], 'status' => [ 'publish', 'draft' ], 'limit' => -1 ] ) as $product ) {
		if ( $product->is_virtual() ) {
			$product->set_virtual( false );
			$product->save();
			WP_CLI::log( "  ~ {$product->get_name()}: fysiek product (bezorgen of afhalen)" );
		}
	}
}
// Bedankpagina na een bestelling: /bedankt/ met het Purchase Summary-widget (Elementor Pro › Site-instellingen › WooCommerce)
$thanks = get_page_by_path( 'bedankt' );
if ( $thanks && (int) get_option( 'elementor_woocommerce_purchase_summary_page_id' ) !== $thanks->ID ) {
	update_option( 'elementor_woocommerce_purchase_summary_page_id', $thanks->ID );
	WP_CLI::log( "  + bedankpagina na bestelling: /bedankt/ ({$thanks->ID})" );
}
// Bedankpagina en betaling mislukt niet in zoekmachines (Yoast)
foreach ( [ 'bedankt', 'betaling-mislukt' ] as $slug ) {
	$p = get_page_by_path( $slug );
	if ( $p && '1' !== get_post_meta( $p->ID, '_yoast_wpseo_meta-robots-noindex', true ) ) {
		update_post_meta( $p->ID, '_yoast_wpseo_meta-robots-noindex', '1' );
		WP_CLI::log( "  + /$slug/ niet indexeren" );
	}
}
WP_CLI::success( 'Winkelinstellingen gezet.' );
