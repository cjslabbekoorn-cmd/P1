<?php
/**
 * Sampark — donatiebedrag als prijs
 *
 * Plaatsen via Snippets → Nieuwe snippet toevoegen.
 * Type: "Alleen PHP uitvoeren" / "Run everywhere".
 * De openingstag <?php hierboven NIET meeplakken als Code Snippets
 * die zelf al toont.
 *
 * WAAROM DIT NODIG IS
 * Super Forms kan een dynamische prijs meegeven met de vierde
 * parameter ({id}|{aantal}|none|{prijs}), maar dat werkt alleen met
 * de betaalde WooCommerce-extensie Name Your Price. Die staat niet
 * op deze site, dus die parameter wordt genegeerd en het product
 * houdt zijn vaste prijs.
 *
 * Wat wél werkt: Super Forms schrijft de custom meta data mee als
 * winkelwagen-meta. Gecontroleerd op een testbestelling van EUR 25:
 *
 *   item_data: [{ name: "Donatiebedrag", value: "25,00" }]
 *
 * Dit snippet leest die regel uit en zet daarmee de prijs, vlak
 * voordat WooCommerce de totalen berekent.
 *
 * BENODIGDE FORMULIERINSTELLING
 * Bij "custom meta data" moet deze regel staan:
 *
 *   {product_id}|Donatiebedrag|{subtotal}
 *
 * Het label moet exact overeenkomen met SAMPARK_DONATIE_LABEL
 * hieronder. Wijzig je het label in het formulier, wijzig het dan
 * hier ook.
 */

/** Het label van de metaregel waar het bedrag in staat. */
define( 'SAMPARK_DONATIE_LABEL', 'Donatiebedrag' );

/**
 * Product-ID's waarvoor dit geldt. Laat de array leeg om het toe te
 * passen op elk product dat de metaregel meekrijgt.
 */
function sampark_donatie_producten() {
	// Op slug in plaats van een vast ID (4040 op staging), zodat het op elke omgeving werkt
	$product = get_page_by_path( 'donatie', OBJECT, 'product' );
	return $product ? array( (int) $product->ID ) : array();
}


add_action( 'woocommerce_before_calculate_totals', 'sampark_donatie_prijs_toepassen', 20, 1 );

function sampark_donatie_prijs_toepassen( $cart ) {

	if ( is_admin() && ! defined( 'DOING_AJAX' ) ) {
		return;
	}

	if ( ! is_a( $cart, 'WC_Cart' ) ) {
		return;
	}

	$producten = sampark_donatie_producten();

	foreach ( $cart->get_cart() as $cart_item ) {

		if ( empty( $cart_item['data'] ) || ! is_a( $cart_item['data'], 'WC_Product' ) ) {
			continue;
		}

		$product_id = isset( $cart_item['product_id'] ) ? (int) $cart_item['product_id'] : 0;

		if ( ! empty( $producten ) && ! in_array( $product_id, $producten, true ) ) {
			continue;
		}

		$bedrag = sampark_zoek_bedrag( $cart_item, SAMPARK_DONATIE_LABEL );

		if ( null === $bedrag ) {
			continue;
		}

		/**
		 * set_price werkt met een absolute waarde, dus het maakt niet
		 * uit hoe vaak deze hook afgaat. Het aantal blijft 1, dus de
		 * regel wordt precies het gedoneerde bedrag.
		 */
		$cart_item['data']->set_price( $bedrag );
	}
}


/**
 * Zoekt in de winkelwagenregel naar de metawaarde met het gegeven
 * label. Doorzoekt de array recursief, zodat het blijft werken als
 * Super Forms de structuur ooit anders opbouwt.
 *
 * @return float|null
 */
function sampark_zoek_bedrag( $data, $label ) {

	if ( ! is_array( $data ) ) {
		return null;
	}

	// Patroon: array( 'name' => 'Donatiebedrag', 'value' => '25,00' )
	if ( isset( $data['name'], $data['value'] ) && is_string( $data['name'] ) ) {

		$naam = trim( wp_strip_all_tags( $data['name'] ) );

		if ( 0 === strcasecmp( $naam, $label ) ) {
			return sampark_bedrag_naar_float( $data['value'] );
		}
	}

	foreach ( $data as $sleutel => $waarde ) {

		// Patroon: array( 'Donatiebedrag' => '25,00' )
		if ( is_string( $sleutel )
			&& 0 === strcasecmp( trim( $sleutel ), $label )
			&& ( is_string( $waarde ) || is_numeric( $waarde ) ) ) {

			$gevonden = sampark_bedrag_naar_float( $waarde );

			if ( null !== $gevonden ) {
				return $gevonden;
			}
		}

		$gevonden = sampark_zoek_bedrag( $waarde, $label );

		if ( null !== $gevonden ) {
			return $gevonden;
		}
	}

	return null;
}


/**
 * Zet een bedrag als "25,00", "1.250,50" of "25.00" om naar een
 * float. Super Forms levert Nederlandse notatie met een komma als
 * decimaalteken en een punt als duizendtalscheiding.
 *
 * @return float|null  null als er geen bruikbaar bedrag in staat
 */
function sampark_bedrag_naar_float( $waarde ) {

	$tekst = trim( wp_strip_all_tags( (string) $waarde ) );
	$tekst = preg_replace( '/[^0-9.,]/', '', $tekst );

	if ( '' === $tekst ) {
		return null;
	}

	$komma = strrpos( $tekst, ',' );
	$punt  = strrpos( $tekst, '.' );

	if ( false !== $komma && false !== $punt ) {

		// Allebei aanwezig: het laatste teken is de decimaalscheiding.
		if ( $komma > $punt ) {
			$tekst = str_replace( '.', '', $tekst );
			$tekst = str_replace( ',', '.', $tekst );
		} else {
			$tekst = str_replace( ',', '', $tekst );
		}
	} elseif ( false !== $komma ) {

		// Alleen een komma: decimaalscheiding bij hoogstens 2 cijfers erachter.
		$achter = strlen( $tekst ) - $komma - 1;

		if ( $achter > 0 && $achter <= 2 ) {
			$tekst = str_replace( ',', '.', $tekst );
		} else {
			$tekst = str_replace( ',', '', $tekst );
		}
	} elseif ( false !== $punt ) {

		// Alleen een punt met precies 3 cijfers erachter is een
		// duizendtalscheiding: "1.250" is 1250, niet 1,25.
		$achter = strlen( $tekst ) - $punt - 1;

		if ( 3 === $achter ) {
			$tekst = str_replace( '.', '', $tekst );
		}
	}

	$bedrag = (float) $tekst;

	return $bedrag > 0 ? $bedrag : null;
}


/**
 * Ook bij het laden van de winkelwagen uit de sessie de prijs zetten. Anders toont
 * het mini-winkelwagentje in de header nog de vaste prijs (die rendert vóór de
 * totaalberekening).
 */
add_filter( 'woocommerce_get_cart_item_from_session', 'sampark_donatie_prijs_uit_sessie', 20, 1 );

function sampark_donatie_prijs_uit_sessie( $cart_item ) {

	$producten  = sampark_donatie_producten();
	$product_id = isset( $cart_item['product_id'] ) ? (int) $cart_item['product_id'] : 0;

	if ( empty( $cart_item['data'] ) || ! is_a( $cart_item['data'], 'WC_Product' )
		|| ( ! empty( $producten ) && ! in_array( $product_id, $producten, true ) ) ) {
		return $cart_item;
	}

	$bedrag = sampark_zoek_bedrag( $cart_item, SAMPARK_DONATIE_LABEL );

	if ( null !== $bedrag ) {
		$cart_item['data']->set_price( $bedrag );
	}

	return $cart_item;
}
