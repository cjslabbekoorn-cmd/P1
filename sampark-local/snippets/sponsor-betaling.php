<?php
/**
 * Sampark — deelname via sponsorpakket (vervangt de regel "Sponsorpakket" uit Woo Discount Rules)
 *
 * Plaatsen via Snippets → Nieuwe snippet toevoegen.
 * Type: "Overal uitvoeren" / "Run everywhere".
 *
 * WAT HET DOET
 * Sponsors met een Sona- of Chandee-pakket doen gratis mee aan het golftoernooi
 * en/of de Sampark Rally. Ze schrijven zich gewoon in via het formulier en kiezen
 * bij het afrekenen de betaalmethode SAMPARK_SPONSOR_METHODE (de WooCommerce-
 * methode "cheque", in de instellingen hernoemd naar bv. "Inbegrepen in mijn
 * sponsorpakket"). Dan worden de deelnameproducten op € 0 gezet.
 *
 * Op staging deed Woo Discount Rules dit met 100% korting op de producten 3656
 * (Golftoernooi) en 4614. Product 4614 bestaat niet meer, waardoor het huidige
 * rallyticket (5841) niet meer meedeed. Hier gaat het op slug, dus een nieuw
 * rallyticket met dezelfde slug valt er automatisch onder.
 *
 * WERKT MET de klassieke afrekenpagina ([woocommerce_checkout]). Bij het wisselen
 * van betaalmethode wordt het totaal opnieuw berekend.
 */

/** De betaalmethode die "betaald via sponsorpakket" betekent. */
define( 'SAMPARK_SPONSOR_METHODE', 'cheque' );

/** Producten (slugs) waarvoor deelname via het sponsorpakket geldt. */
function sampark_sponsor_producten() {
	$ids = array();
	foreach ( array( 'golftoernooi', 'ticket-sampark-rally', 'ticket-samparkrally-2026' ) as $slug ) {
		$product = get_page_by_path( $slug, OBJECT, 'product' );
		if ( $product ) {
			$ids[] = (int) $product->ID;
		}
	}
	return $ids;
}

/** Is op dit moment de sponsorbetaalmethode gekozen? */
function sampark_sponsor_methode_gekozen() {
	// Tijdens het afrekenen stuurt WooCommerce de keuze mee (update_order_review / checkout)
	if ( isset( $_POST['payment_method'] ) ) {
		return SAMPARK_SPONSOR_METHODE === sanitize_text_field( wp_unslash( $_POST['payment_method'] ) );
	}
	if ( function_exists( 'WC' ) && WC()->session ) {
		return SAMPARK_SPONSOR_METHODE === WC()->session->get( 'chosen_payment_method' );
	}
	return false;
}

add_action( 'woocommerce_before_calculate_totals', 'sampark_sponsor_deelname_gratis', 30, 1 );

function sampark_sponsor_deelname_gratis( $cart ) {

	if ( is_admin() && ! defined( 'DOING_AJAX' ) ) {
		return;
	}

	if ( ! is_a( $cart, 'WC_Cart' ) || ! sampark_sponsor_methode_gekozen() ) {
		return;
	}

	$producten = sampark_sponsor_producten();

	foreach ( $cart->get_cart() as $cart_item ) {
		if ( ! empty( $cart_item['data'] ) && in_array( (int) $cart_item['product_id'], $producten, true ) ) {
			$cart_item['data']->set_price( 0 );
		}
	}
}

/**
 * Betaalmethodes zichtbaar houden als het totaal door deze regel € 0 wordt.
 * Anders verbergt WooCommerce de keuze en kan de bezoeker niet meer terug naar
 * een gewone betaalmethode. De bestelling krijgt zo ook "Inbegrepen in mijn
 * sponsorpakket" als betaalmethode, zodat zichtbaar is waarom hij € 0 is.
 */
add_filter( 'woocommerce_cart_needs_payment', function ( $needs, $cart ) {
	if ( $needs || ! sampark_sponsor_methode_gekozen() ) {
		return $needs;
	}
	$producten = sampark_sponsor_producten();
	foreach ( $cart->get_cart() as $cart_item ) {
		if ( in_array( (int) $cart_item['product_id'], $producten, true ) ) {
			return true;
		}
	}
	return $needs;
}, 10, 2 );

/** Totaal opnieuw laten berekenen zodra de bezoeker een andere betaalmethode kiest. */
add_action( 'wp_footer', function () {
	if ( ! function_exists( 'is_checkout' ) || ! is_checkout() ) {
		return;
	}
	?>
	<script>
	jQuery( function ( $ ) {
		$( 'form.checkout' ).on( 'change', 'input[name="payment_method"]', function () {
			$( document.body ).trigger( 'update_checkout' );
		} );
	} );
	</script>
	<?php
} );
