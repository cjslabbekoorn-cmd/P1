<?php
/**
 * Sampark — pagina bij een mislukte of afgebroken betaling (/betaling-mislukt/)
 *
 * Plaatsen via Snippets → Nieuwe snippet toevoegen.
 * Type: "Overal uitvoeren" / "Run everywhere".
 *
 * WAT HET DOET
 * Komt een klant na het betalen op de bedankpagina terwijl de bestelling "Mislukt" of
 * "Geannuleerd" is (bv. iDEAL afgebroken of geweigerd), dan sturen we door naar
 * /betaling-mislukt/ in plaats van "Bedankt voor jouw steun!" te tonen.
 * Die pagina toont met de shortcode [sampark_betaling_mislukt] het bestelnummer, het
 * bedrag en een knop "Opnieuw betalen" (de betaalpagina van WooCommerce, waar de klant
 * ook een andere betaalmethode zoals op factuur kan kiezen).
 *
 * De bestelling wordt alleen getoond met de juiste bestelsleutel uit de link.
 */

/** Het pad van de pagina voor een mislukte betaling. */
define( 'SAMPARK_MISLUKT_PAD', 'betaling-mislukt' );

/** Bestelling uit de link (?bestelling=ID&key=wc_order_…), alleen met de juiste sleutel. */
function sampark_mislukt_bestelling() {
	$id  = isset( $_GET['bestelling'] ) ? absint( $_GET['bestelling'] ) : 0;
	$key = isset( $_GET['key'] ) ? wc_clean( wp_unslash( $_GET['key'] ) ) : '';
	$order = ( $id && $key && function_exists( 'wc_get_order' ) ) ? wc_get_order( $id ) : false;
	return ( $order && hash_equals( $order->get_order_key(), $key ) ) ? $order : false;
}

// Bedankpagina bij een mislukte of geannuleerde bestelling → /betaling-mislukt/
add_action( 'template_redirect', function () {
	// is_wc_endpoint_url en niet is_order_received_page: de bedankpagina is /bedankt/ (Elementor Pro), niet afrekenen
	if ( ! function_exists( 'is_wc_endpoint_url' ) || ! is_wc_endpoint_url( 'order-received' ) ) {
		return;
	}
	$order = wc_get_order( absint( get_query_var( 'order-received' ) ) );
	$key   = isset( $_GET['key'] ) ? wc_clean( wp_unslash( $_GET['key'] ) ) : '';
	$page  = get_page_by_path( SAMPARK_MISLUKT_PAD );
	if ( ! $order || ! $page || ! hash_equals( $order->get_order_key(), $key ) || ! $order->has_status( array( 'failed', 'cancelled' ) ) ) {
		return;
	}
	wp_safe_redirect( add_query_arg( array( 'bestelling' => $order->get_id(), 'key' => $key ), get_permalink( $page ) ) );
	exit;
} );

// [sampark_betaling_mislukt]: bestelnummer, bedrag en de knop om opnieuw te betalen
add_shortcode( 'sampark_betaling_mislukt', function () {
	$order = sampark_mislukt_bestelling();
	if ( ! $order ) {
		return '<div class="sp-mislukt"><p>Ga terug naar je winkelwagen om je bestelling opnieuw af te ronden.</p>'
			. '<p><a class="elementor-button sp-mislukt-knop" href="' . esc_url( wc_get_cart_url() ) . '">Naar je winkelwagen</a></p></div>';
	}

	$items = array();
	foreach ( $order->get_items() as $item ) {
		$items[] = esc_html( $item->get_name() ) . ( $item->get_quantity() > 1 ? ' × ' . (int) $item->get_quantity() : '' );
	}

	$html  = '<div class="sp-mislukt">';
	$html .= '<ul class="sp-mislukt-gegevens">';
	$html .= '<li>Bestelnummer<strong>' . esc_html( $order->get_order_number() ) . '</strong></li>';
	$html .= '<li>Bedrag<strong>' . wp_kses_post( $order->get_formatted_order_total() ) . '</strong></li>';
	$html .= '<li>Status<strong>' . ( $order->has_status( 'cancelled' ) ? 'Geannuleerd' : 'Niet betaald' ) . '</strong></li>';
	$html .= '</ul>';
	if ( $items ) {
		$html .= '<p class="sp-mislukt-items">' . implode( '<br>', $items ) . '</p>';
	}

	if ( $order->needs_payment() ) {
		// Mislukt: de bestelling staat nog open en kan opnieuw betaald worden
		$html .= '<p><a class="elementor-button sp-mislukt-knop" href="' . esc_url( $order->get_checkout_payment_url() ) . '">Opnieuw betalen</a></p>';
		$html .= '<p class="sp-mislukt-noot">Je kunt daar ook een andere betaalmethode kiezen, bijvoorbeeld op factuur.</p>';
	} else {
		// Geannuleerd: niet meer te betalen, dus opnieuw bestellen
		$product = null;
		foreach ( $order->get_items() as $item ) {
			$product = $item->get_product();
			break;
		}
		$url   = $product ? $product->get_permalink() : wc_get_cart_url();
		$html .= '<p><a class="elementor-button sp-mislukt-knop" href="' . esc_url( $url ) . '">Opnieuw bestellen</a></p>';
		$html .= '<p class="sp-mislukt-noot">Deze bestelling is geannuleerd. Vul het formulier opnieuw in om alsnog te bestellen.</p>';
	}
	return $html . '</div>';
} );
