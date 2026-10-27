<?php
/**
 * Sampark — regelgegevens op factuur en pakbon
 *
 * Plaatsen via Snippets → Nieuwe snippet toevoegen.
 * Type: "Alleen PHP uitvoeren" / "Run everywhere".
 * De openingstag <?php hierboven NIET meeplakken als Code Snippets
 * die zelf al toont.
 *
 * FACTUUR — alleen de metaregels waarvan het label matcht met
 *           $bewaren blijven staan.
 *
 * PAKBON  — regels die het patroon "Speler N - veld" volgen worden
 *           samengevoegd tot een tabel met een rij per deelnemer en
 *           een kolom per veld. Dat is compacter en leest logisch,
 *           in plaats van gegevens die van links naar rechts over
 *           meerdere regels verspreid raken.
 *
 * De filter wpo_wcpdf_order_item_data krijgt het documenttype mee,
 * zodat per document bepaald kan worden wat er getoond wordt.
 */

add_filter( 'wpo_wcpdf_order_item_data', 'sampark_regelgegevens', 10, 3 );

function sampark_regelgegevens( $data, $order, $document_type ) {

	if ( empty( $data['meta'] ) ) {
		return $data;
	}

	if ( 'packing-slip' === $document_type ) {
		return sampark_pakbon_deelnemertabel( $data );
	}

	if ( 'invoice' !== $document_type ) {
		return $data;
	}

	/**
	 * Welke labels blijven staan op de factuur.
	 * Voeg termen toe, gescheiden door een pipe.
	 */
	$bewaren = '/(-\s*naam|Gewenste leverdatum)/i';

	$regels = '';

	foreach ( sampark_meta_paren( $data ) as $paar ) {

		if ( ! preg_match( $bewaren, $paar['label'] ) ) {
			continue;
		}

		$regels .= '<li><strong class="wc-item-meta-label">'
			. esc_html( $paar['label'] ) . ':</strong> '
			. esc_html( $paar['waarde'] ) . '</li>';
	}

	$data['meta'] = $regels ? '<ul class="wc-item-meta">' . $regels . '</ul>' : '';

	return $data;
}


/**
 * Haalt de regelgegevens op als platte label/waarde-paren.
 *
 * display_value bevat <p>-tags en soms een mailto-link. Een <p> is
 * een blokelement en zakt in dompdf onder het label, dus alles wordt
 * hier tot platte tekst teruggebracht.
 */
function sampark_meta_paren( $data ) {

	$paren = array();

	if ( ! empty( $data['item'] ) && is_a( $data['item'], 'WC_Order_Item' ) ) {

		foreach ( $data['item']->get_formatted_meta_data( '_', true ) as $meta ) {

			$label  = trim( wp_strip_all_tags( $meta->display_key ) );
			$waarde = trim( wp_strip_all_tags( $meta->display_value ) );

			if ( '' === $label || '' === $waarde ) {
				continue;
			}

			$paren[] = array(
				'label'  => $label,
				'waarde' => $waarde,
			);
		}

		return $paren;
	}

	// Terugvaloptie: het order item zit niet in $data.
	if ( preg_match_all( '/<li>(.*?)<\/li>/is', $data['meta'], $treffers ) ) {

		foreach ( $treffers[1] as $regel ) {

			$plat = trim( wp_strip_all_tags( $regel ) );
			$deel = explode( ':', $plat, 2 );

			if ( count( $deel ) < 2 || '' === trim( $deel[1] ) ) {
				continue;
			}

			$paren[] = array(
				'label'  => trim( $deel[0] ),
				'waarde' => trim( $deel[1] ),
			);
		}
	}

	return $paren;
}


/**
 * Bouwt de pakbonregels om tot een tabel met een rij per deelnemer.
 */
function sampark_pakbon_deelnemertabel( $data ) {

	$paren = sampark_meta_paren( $data );

	if ( empty( $paren ) ) {
		return $data;
	}

	$deelnemers = array();  // [ "Speler 1" => [ veld => waarde ] ]
	$kolommen   = array();  // veldnamen in volgorde van voorkomen
	$overig     = array();  // alles wat het patroon niet volgt

	foreach ( $paren as $paar ) {

		if ( preg_match( '/^(.+?)\s*-\s*(.+)$/u', $paar['label'], $m ) ) {

			$deelnemer = trim( $m[1] );
			$veld      = trim( $m[2] );

			$deelnemers[ $deelnemer ][ $veld ] = $paar['waarde'];

			if ( ! in_array( $veld, $kolommen, true ) ) {
				$kolommen[] = $veld;
			}

			continue;
		}

		$overig[] = $paar;
	}

	// Minder dan twee deelnemers: de tabel levert niets op.
	if ( count( $deelnemers ) < 2 ) {
		return sampark_pakbon_eenvoudige_lijst( $data, $paren );
	}

	$kolommen = sampark_kolommen_sorteren( $kolommen );

	/**
	 * Raster van kaartjes: twee deelnemers naast elkaar, de rest
	 * eronder. Per kaartje staan de velden onder elkaar, zodat de
	 * gegevens van een deelnemer bij elkaar blijven en er geen
	 * brede kolommen nodig zijn.
	 */
	$per_rij = 2;
	$namen   = array_keys( $deelnemers );

	$html = '<table class="deelnemers-grid"><tbody>';

	foreach ( array_chunk( $namen, $per_rij ) as $groep ) {

		$html .= '<tr>';

		foreach ( $groep as $naam ) {

			$html .= '<td class="kaart"><table class="deelnemer">'
				. '<tr><th colspan="2" class="kop">' . esc_html( $naam ) . '</th></tr>';

			foreach ( $kolommen as $veld ) {

				if ( ! isset( $deelnemers[ $naam ][ $veld ] ) ) {
					continue;
				}

				$html .= '<tr><th>' . esc_html( sampark_kolom_kop( $veld ) ) . '</th>'
					. '<td>' . esc_html( $deelnemers[ $naam ][ $veld ] ) . '</td></tr>';
			}

			$html .= '</table></td>';
		}

		// Rij aanvullen zodat de kolommen even breed blijven.
		for ( $n = count( $groep ); $n < $per_rij; $n++ ) {
			$html .= '<td class="kaart"></td>';
		}

		$html .= '</tr>';
	}

	$html .= '</tbody></table>';

	// Regels die niet bij een deelnemer horen eronder zetten.
	if ( ! empty( $overig ) ) {

		$html .= '<ul class="wc-item-meta">';

		foreach ( $overig as $paar ) {
			$html .= '<li><strong class="wc-item-meta-label">'
				. esc_html( $paar['label'] ) . ':</strong> '
				. esc_html( $paar['waarde'] ) . '</li>';
		}

		$html .= '</ul>';
	}

	$data['meta'] = $html;

	return $data;
}


/**
 * Eén deelnemer of losse regels: gewoon een lijst, geen tabel.
 */
function sampark_pakbon_eenvoudige_lijst( $data, $paren ) {

	$regels = '';

	foreach ( $paren as $paar ) {
		$regels .= '<li><strong class="wc-item-meta-label">'
			. esc_html( $paar['label'] ) . ':</strong> '
			. esc_html( $paar['waarde'] ) . '</li>';
	}

	$data['meta'] = $regels ? '<ul class="wc-item-meta">' . $regels . '</ul>' : '';

	return $data;
}


/**
 * Vaste kolomvolgorde. Zonder dit bepaalt toeval de volgorde:
 * een veld dat bij de eerste deelnemer leeg is, komt anders pas
 * later in de rij terecht.
 *
 * Velden die hier niet in staan, komen erachteraan in de volgorde
 * waarin ze voorkomen.
 */
function sampark_kolommen_sorteren( $kolommen ) {

	$voorkeur = array(
		'naam',
		'e-mail',
		'telefoon',
		'handicap',
		'handicapwaarde',
		'diner',
		'onderdeel',
	);

	$gesorteerd = array();

	foreach ( $voorkeur as $veld ) {
		foreach ( $kolommen as $bestaand ) {
			if ( 0 === strcasecmp( trim( $bestaand ), $veld ) ) {
				$gesorteerd[] = $bestaand;
			}
		}
	}

	foreach ( $kolommen as $bestaand ) {
		if ( ! in_array( $bestaand, $gesorteerd, true ) ) {
			$gesorteerd[] = $bestaand;
		}
	}

	return $gesorteerd;
}


/**
 * Maakt van een veldnaam een CSS-klasse, zodat kolombreedtes in de
 * stylesheet per veld ingesteld kunnen worden.
 */
function sampark_kolom_klasse( $veld ) {

	$slug = strtolower( trim( $veld ) );
	$slug = str_replace( array( ' ', '-' ), '', $slug );
	$slug = preg_replace( '/[^a-z0-9]/', '', $slug );

	return 'col-' . $slug;
}


/**
 * Kortere koppen voor de smalle kolommen. Een lange kop maakt de
 * kolom breder dan nodig of wordt door dompdf afgekapt.
 */
function sampark_kolom_kop( $veld ) {

	$kort = array(
		'handicapwaarde' => 'Hcp-waarde',
		'e-mail'         => 'E-mail',
		'telefoon'       => 'Telefoon',
	);

	$sleutel = strtolower( trim( $veld ) );

	if ( isset( $kort[ $sleutel ] ) ) {
		return $kort[ $sleutel ];
	}

	return ucfirst( $veld );
}
