#!/bin/sh
# Bouwt een lege Sampark-basis volgens het structuurvoorstel.
# Draai vanuit sampark-local/:  docker compose run --rm wpcli sh /scripts/setup.sh
# Het script is herhaalbaar: wat al bestaat wordt overgeslagen.
set -eu

wp() { command wp --path=/var/www/html "$@"; }
log() { printf '\n==> %s\n' "$*"; }

if [ ! -f /var/www/html/wp-config.php ]; then
	echo "wp-config.php ontbreekt. Start eerst de site: docker compose up -d" >&2
	exit 1
fi

# ---------------------------------------------------------------- core
if ! wp core is-installed 2>/dev/null; then
	log "WordPress installeren"
	wp core install --url="$WP_URL" --title="Stichting Sampark" \
		--admin_user="$WP_ADMIN_USER" --admin_password="$WP_ADMIN_PASSWORD" \
		--admin_email="$WP_ADMIN_EMAIL" --skip-email
fi

log "Taal en instellingen"
wp language core install nl_NL --activate >/dev/null 2>&1 || true
wp option update timezone_string "Europe/Amsterdam"
wp option update date_format "j F Y"
wp option update blog_public 0
wp option update default_comment_status closed
wp rewrite structure '/%postname%/' --hard

log "Standaardinhoud opruimen"
for slug in hallo-wereld hello-world voorbeeld-pagina sample-page; do
	for id in $(wp post list --post_type=post,page --name="$slug" --field=ID); do wp post delete "$id" --force; done
done
wp plugin delete akismet hello >/dev/null 2>&1 || true

# ---------------------------------------------------------------- thema + plugins
log "Thema en gratis plugins"
wp theme install hello-elementor --activate
# Elementor gelijk aan staging (4.1.5), zodat Elementor Pro 4.1.x van staging erop past
ELEMENTOR_VERSION="${ELEMENTOR_VERSION:-4.1.5}"
if [ "$(wp plugin get elementor --field=version 2>/dev/null || true)" != "$ELEMENTOR_VERSION" ]; then
	wp plugin install elementor --version="$ELEMENTOR_VERSION" --force
fi
wp plugin activate elementor
# Vaste plugins (zie README › Plugins). Ultimate Dashboard en Woo Discount Rules zitten er bewust niet in.
for p in woocommerce wordpress-seo redirection mailchimp-for-woocommerce duracelltomi-google-tag-manager code-snippets; do
	wp plugin is-installed "$p" || wp plugin install "$p"
	wp plugin activate "$p"
done
wp language plugin install --all nl_NL >/dev/null 2>&1 || true
wp language theme install --all nl_NL >/dev/null 2>&1 || true
wp theme delete twentytwentythree twentytwentyfour twentytwentyfive >/dev/null 2>&1 || true

log "Premium plugins uit plugins/premium/ (zips of mappen, bv. via FTP van staging)"
found=0
for zip in /premium/*.zip; do
	[ -e "$zip" ] || continue
	found=1
	echo "  $zip"
	# Zelf uitpakken: zips van een Mac bevatten een __MACOSX-map die wp plugin install in de war brengt
	tmp=$(mktemp -d)
	export SP_ZIP="$zip" SP_TMP="$tmp"
	wp eval 'WP_Filesystem(); $r = unzip_file( getenv( "SP_ZIP" ), getenv( "SP_TMP" ) ); if ( is_wp_error( $r ) ) { WP_CLI::error( $r->get_error_message() ); }'
	for pdir in "$tmp"/*/; do
		slug=$(basename "$pdir")
		[ "$slug" = "__MACOSX" ] && continue
		ls "$pdir"*.php >/dev/null 2>&1 || continue
		mkdir -p "/var/www/html/wp-content/plugins/$slug"
		cp -R "$pdir." "/var/www/html/wp-content/plugins/$slug/"
		wp plugin activate "$slug"
	done
	rm -r "$tmp"
done
for dir in /premium/*/; do
	ls "$dir"*.php >/dev/null 2>&1 || continue
	slug=$(basename "$dir")
	[ -n "$slug" ] || continue
	found=1
	echo "  $slug/ (map)"
	mkdir -p "/var/www/html/wp-content/plugins/$slug"
	cp -R "$dir." "/var/www/html/wp-content/plugins/$slug/"
	wp plugin activate "$slug"
done
[ "$found" = 1 ] || echo "  Niets gevonden. Zet Elementor Pro, JetEngine en Super Forms (zip of map) in plugins/premium/ en draai dit script opnieuw."

# Google Tag Manager alleen als GTM_ID is gezet (lokaal standaard uit, zodat er geen testverkeer in de statistieken komt)
if [ -n "${GTM_ID:-}" ]; then
	wp eval '$o = get_option( "gtm4wp-options", [] ); $o = is_array( $o ) ? $o : []; $o["gtm-code"] = getenv( "GTM_ID" ); update_option( "gtm4wp-options", $o );'
	echo "  GTM-container ${GTM_ID} ingesteld"
fi

# Adobe Fonts (Aptos). Elementor Pro laadt de kit zelf via deze instelling;
# zonder Pro laadt mu-plugins/sampark-styles.php hem.
wp option update elementor_typekit-kit-id "${ADOBE_FONTS_PROJECT:-nnd7fbm}" >/dev/null

# ---------------------------------------------------------------- WooCommerce
log "WooCommerce"
wp option update woocommerce_default_country "NL"
wp option update woocommerce_currency "EUR"
wp option update woocommerce_price_thousand_sep "."
wp option update woocommerce_price_decimal_sep ","
wp option update woocommerce_calc_taxes "no"
wp option update woocommerce_onboarding_profile '{"skipped":true}' --format=json
wp option update woocommerce_coming_soon "no"
wp wc tool run install_pages --user="$WP_ADMIN_USER" >/dev/null

# ---------------------------------------------------------------- pagina's
# page <slug> <titel> [parent-slug]
page_id() { wp post list --post_type=page --name="$1" --post_status=any --field=ID | head -n1; }
page() {
	id=$(page_id "$1")
	if [ -z "$id" ]; then
		parent=0
		[ -n "${3:-}" ] && parent=$(page_id "$3")
		id=$(wp post create --post_type=page --post_status=publish --post_name="$1" \
			--post_title="$2" --post_parent="$parent" --porcelain)
		echo "  + /$1/ ($id)" >&2
	fi
	echo "$id"
}

log "Huisstijl, beelden en pagina's (bouwplan v2)"
wp eval-file /scripts/build-site.php


NIEUWS_ID=$(page nieuws "Nieuws")
VOORW_ID=$(page algemene-voorwaarden "Algemene voorwaarden")
page sitemap "Sitemap" >/dev/null
HOME_ID=$(page_id home)
STEUN_ID=$(page_id steun-ons)
DONEER_ID=$(page_id doneren)
BEDRIJF_ID=$(page_id bedrijven)
WERK_ID=$(page_id ons-werk)
EVENT_ID=$(page_id evenementen)
OVER_ID=$(page_id over-ons)
ANBI_ID=$(page_id anbi)
CONTACT_ID=$(page_id contact)

# Pagina's uit het eerste voorstel die in v2 zijn opgegaan in Steun ons
for slug in sponsors; do
	for id in $(wp post list --post_type=page --name="$slug" --post_status=any --field=ID); do wp post delete "$id" --force >/dev/null; done
done

# Privacybeleid van WordPress zelf hergebruiken
PRIVACY_ID=$(wp option get wp_page_for_privacy_policy)
if [ -n "$PRIVACY_ID" ] && [ "$PRIVACY_ID" != 0 ]; then
	wp post update "$PRIVACY_ID" --post_status=publish --post_title="Privacyverklaring" --post_name=privacyverklaring >/dev/null
fi

wp option update show_on_front page
wp option update page_on_front "$HOME_ID"
wp option update page_for_posts "$NIEUWS_ID"

# Woo-shoppagina heet op live /shop/; die blijft bestaan maar wordt niet gelinkt
SHOP_ID=$(wp option get woocommerce_shop_page_id)
wp post update "$SHOP_ID" --post_name=shop --post_title="Shop" >/dev/null
wp option update woocommerce_terms_page_id "$VOORW_ID"
wp post update "$(wp option get woocommerce_cart_page_id)" --post_name=winkelwagen --post_title="Winkelwagen" >/dev/null
wp post update "$(wp option get woocommerce_checkout_page_id)" --post_name=afrekenen --post_title="Afrekenen" >/dev/null
wp post update "$(wp option get woocommerce_myaccount_page_id)" --post_name=mijn-account --post_title="Mijn account" >/dev/null
REFUND_ID=$(wp option get woocommerce_refund_returns_page_id 2>/dev/null || true)
if [ -n "$REFUND_ID" ] && [ "$REFUND_ID" != 0 ]; then
	wp post delete "$REFUND_ID" --force >/dev/null 2>&1 || true
	wp option update woocommerce_refund_returns_page_id 0 >/dev/null
fi

# ---------------------------------------------------------------- nieuwscategorieën
log "Nieuwscategorieën"
cat_id() { wp term list category --slug="$1" --field=term_id | head -n1; }
newscat() {
	[ -n "$(cat_id "$1")" ] || wp term create category "$2" --slug="$1" >/dev/null
}
newscat scholen-leerlingen "Scholen & leerlingen"
newscat evenementen "Evenementen"
newscat sponsors-partners "Sponsors & partners"
newscat stichting "Stichting"
wp option update default_category "$(cat_id stichting)"
UNCAT=$(cat_id uncategorized); [ -z "$UNCAT" ] && UNCAT=$(cat_id geen-categorie)
[ -n "$UNCAT" ] && [ "$UNCAT" != "$(cat_id stichting)" ] && wp term delete category "$UNCAT" >/dev/null 2>&1 || true

# ---------------------------------------------------------------- producten
log "Productcategorieën en producten"
pcat_id() { wp term list product_cat --slug="$1" --field=term_id | head -n1; }
pcat() {
	[ -n "$(pcat_id "$1")" ] || wp term create product_cat "$2" --slug="$1" >/dev/null
	pcat_id "$1"
}
C_DONATIE=$(pcat donatie "Donatie")
C_PAKKET=$(pcat sponsorpakket "Sponsorpakket")
C_WIJN=$(pcat wijnactie "Wijnactie")
C_RALLY=$(pcat samparkrally "Sampark Rally")
C_GOLF=$(pcat golftoernooi "Golftoernooi")
pcat padel "Padel toernooi" >/dev/null
wp term delete product_cat "$(pcat_id uncategorized)" >/dev/null 2>&1 || true

# product <slug> <titel> <prijs> <categorie-id> <korte omschrijving> [status]
product() {
	# op titel zoeken: concepten hebben nog geen slug
	if [ -n "$(wp post list --post_type=product --title="$2" --post_status=any --field=ID)" ]; then return; fi
	wp wc product create --user="$WP_ADMIN_USER" --slug="$1" --name="$2" \
		--regular_price="$3" --categories="[{\"id\":$4}]" \
		--short_description="$5" --status="${6:-publish}" --virtual=true --porcelain >/dev/null
	echo "  + /product/$1/"
}
product donatie "Eenmalige donatie" 10 "$C_DONATIE" "We zijn blij met iedere donatie."
product sponsor-een-kind "Sponsor een kind" 60 "$C_PAKKET" "U financiert hiermee het lesgeld en verdere schoolbenodigdheden voor één kind gedurende het jaar."
product peetal-brons "Peetal (Brons)" 500 "$C_PAKKET" "Naamsvermelding op onze website, clickable banner van Sampark op uw eigen website en Sampark-uitingen voor eigen MVO-doeleinden."
product chandee-zilver "Chandee (Zilver)" 1750 "$C_PAKKET" "Alle inhoud van het Peetal-pakket + deelname aan het golftoernooi OF de Sampark Rally en naamsvermelding bij dat evenement."
product sona-goud "Sona (Goud)" 2500 "$C_PAKKET" "Alle inhoud van het Peetal-pakket + deelname aan het golftoernooi EN de Sampark Rally en naamsvermelding bij het gekozen evenement."
product rode-wijn "Rode wijn" 43.50 "$C_WIJN" "Per doos (6 flessen)."
product witte-wijn "Witte wijn" 43.50 "$C_WIJN" "Per doos (6 flessen)."
product alcoholvrij "Alcoholvrij mousserend" 0 "$C_WIJN" "Per doos (6 flessen). Prijs nog invullen." draft
product ticket-sampark-rally "Ticket Sampark Rally" 600 "$C_RALLY" "1 ticket per auto, twee deelnemers."
product golftoernooi "Golftoernooi" 300 "$C_GOLF" "Per deelnemer. Een tafel voor 4 personen is € 1.200."

# ---------------------------------------------------------------- JetEngine
# Na de nieuwscategorieën en producten, want de inhoud en queries verwijzen daarnaar
if wp plugin is-active code-snippets; then
	log "Code Snippets: factuuropmaak, donatieprijs en sponsorbetaling"
	wp eval-file /scripts/snippets-import.php
fi

# Afrekenen: klassieke winkelwagen en checkout, want de sponsorregel herberekent bij wisselen van betaalmethode.
# "cheque" heet in de winkel "Inbegrepen in mijn sponsorpakket"; "bacs" (bankoverschrijving uit WooCommerce zelf) is "Op factuur".
# iDEAL komt op staging/live uit Mollie.
wp post update "$(wp option get woocommerce_cart_page_id)" --post_content='<!-- wp:shortcode -->[woocommerce_cart]<!-- /wp:shortcode -->' >/dev/null
wp post update "$(wp option get woocommerce_checkout_page_id)" --post_content='<!-- wp:shortcode -->[woocommerce_checkout]<!-- /wp:shortcode -->' >/dev/null
wp option update woocommerce_cheque_settings '{"enabled":"yes","title":"Inbegrepen in mijn sponsorpakket","description":"Alleen voor sponsors met een Sona- of Chandee-pakket: deelname aan het golftoernooi of de rally zit in je pakket.","instructions":""}' --format=json >/dev/null
wp option update woocommerce_bacs_settings '{"enabled":"yes","title":"Op factuur","description":"Je ontvangt de bestelbevestiging met onze bankgegevens per e-mail. Maak het bedrag binnen 14 dagen over.","instructions":"Maak het bedrag binnen 14 dagen over onder vermelding van het bestelnummer. Je deelname of bestelling is definitief zodra de betaling binnen is."}' --format=json >/dev/null
wp option update woocommerce_bacs_accounts '[{"account_name":"Stichting Sampark","account_number":"","bank_name":"ABN AMRO","sort_code":"","iban":"NL25 ABNA 0578 9231 73","bic":"ABNANL2A"}]' --format=json >/dev/null

if wp plugin is-active super-forms; then
	log "Super Forms: de vier formulieren van staging"
	wp eval-file /scripts/superforms-import.php 2>&1 | grep -v SERVER_NAME || true
fi

if wp plugin is-active jet-engine; then
	log "JetEngine: posttypes, velden, relaties, Options Page, queries, listings en inhoud"
	# twee keer: queries die in de eerste ronde zijn aangemaakt, zijn pas in de tweede ronde geladen
	wp eval-file /scripts/jetengine-setup.php
	wp eval-file /scripts/jetengine-setup.php >/dev/null
	log "Pagina's opnieuw opbouwen met JetEngine Listing Grids en Map Listing"
	wp eval-file /scripts/build-site.php >/dev/null
	wp rewrite flush --hard >/dev/null 2>&1 || true
fi

# ---------------------------------------------------------------- menu's
log "Menu's"
# menu <naam>: maakt het menu (opnieuw) aan en geeft het id terug
menu() {
	old=$(wp term list nav_menu --name="$1" --field=term_id | head -n1)
	[ -z "$old" ] || wp menu delete "$old" >/dev/null
	wp menu create "$1" --porcelain
}
M=$(menu "Hoofdmenu")
wp menu item add-post "$M" "$WERK_ID" >/dev/null
wp menu item add-post "$M" "$EVENT_ID" >/dev/null
STEUN_ITEM=$(wp menu item add-post "$M" "$STEUN_ID" --porcelain)
for id in "$DONEER_ID" "$BEDRIJF_ID"; do wp menu item add-post "$M" "$id" --parent-id="$STEUN_ITEM" >/dev/null; done
wp menu item add-custom "$M" "Sponsor een kind" "/product/sponsor-een-kind/" --parent-id="$STEUN_ITEM" >/dev/null
wp menu item add-post "$M" "$NIEUWS_ID" >/dev/null
OVER_ITEM=$(wp menu item add-post "$M" "$OVER_ID" --porcelain)
for id in "$ANBI_ID" "$CONTACT_ID"; do wp menu item add-post "$M" "$id" --parent-id="$OVER_ITEM" >/dev/null; done
wp menu location assign "$M" menu-1 >/dev/null 2>&1 || true

M=$(menu "Topbalk")
wp menu item add-post "$M" "$BEDRIJF_ID" --title="Voor bedrijven" >/dev/null
wp menu item add-post "$M" "$CONTACT_ID" >/dev/null
wp menu item add-post "$M" "$(wp option get woocommerce_myaccount_page_id)" >/dev/null

M=$(menu "Footer – Direct naar")
for id in "$WERK_ID" "$EVENT_ID" "$DONEER_ID" "$BEDRIJF_ID" "$ANBI_ID" "$CONTACT_ID"; do
	wp menu item add-post "$M" "$id" >/dev/null
done
wp menu location assign "$M" menu-2 >/dev/null 2>&1 || true

M=$(menu "Footer – Juridisch")
for id in "$VOORW_ID" "$PRIVACY_ID" "$(page_id sitemap)"; do
	if [ -n "$id" ] && [ "$id" != 0 ]; then wp menu item add-post "$M" "$id" >/dev/null; fi
done

wp rewrite flush --hard >/dev/null 2>&1 || true

log "Klaar"
cat <<EOF

  Site:        $WP_URL
  Beheer:      $WP_URL/wp-admin  ($WP_ADMIN_USER / $WP_ADMIN_PASSWORD)
  phpMyAdmin:  http://localhost:8081
  Mail:        http://localhost:8025

  Volgende stap: JetEngine-structuur aanmaken (zie README.md, "Handmatig in JetEngine").
EOF
