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
for p in woocommerce elementor wordpress-seo redirection; do
	wp plugin is-installed "$p" || wp plugin install "$p"
	wp plugin activate "$p"
done
wp language plugin install --all nl_NL >/dev/null 2>&1 || true
wp language theme install --all nl_NL >/dev/null 2>&1 || true
wp theme delete twentytwentythree twentytwentyfour twentytwentyfive >/dev/null 2>&1 || true

log "Premium plugins uit plugins/premium/"
found=0
for zip in /premium/*.zip; do
	[ -e "$zip" ] || continue
	found=1
	echo "  $zip"
	wp plugin install "$zip" --activate --force
done
[ "$found" = 1 ] || echo "  Geen zips gevonden. Zet Elementor Pro, JetEngine en Super Forms in plugins/premium/ en draai dit script opnieuw."

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

log "Pagina's volgens structuurvoorstel"
HOME_ID=$(page home "Home")
NIEUWS_ID=$(page nieuws "Nieuws")
STEUN_ID=$(page steun-ons "Steun ons")
SPONSORS_ID=$(page sponsors "Sponsors")
OVER_ID=$(page over-ons "Over ons")
ANBI_ID=$(page anbi "ANBI & financiën" over-ons)
CONTACT_ID=$(page contact "Contact")
VOORW_ID=$(page algemene-voorwaarden "Algemene voorwaarden")
page sitemap "Sitemap" >/dev/null

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

# ---------------------------------------------------------------- menu's
log "Menu's"
# menu <naam>: maakt het menu (opnieuw) aan en geeft het id terug
menu() {
	old=$(wp term list nav_menu --name="$1" --field=term_id | head -n1)
	[ -z "$old" ] || wp menu delete "$old" >/dev/null
	wp menu create "$1" --porcelain
}
M=$(menu "Hoofdmenu")
wp menu item add-custom "$M" "Projecten" "/projecten/" >/dev/null
wp menu item add-custom "$M" "Evenementen" "/evenementen/" >/dev/null
for id in "$STEUN_ID" "$NIEUWS_ID" "$OVER_ID"; do wp menu item add-post "$M" "$id" >/dev/null; done

M=$(menu "Footer – Direct naar")
for id in "$STEUN_ID" "$SPONSORS_ID" "$ANBI_ID" "$CONTACT_ID" "$(wp option get woocommerce_myaccount_page_id)"; do
	wp menu item add-post "$M" "$id" >/dev/null
done

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
