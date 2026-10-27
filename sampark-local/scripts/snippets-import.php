<?php
/**
 * Zet de snippets uit snippets/*.php in Code Snippets (aan, "overal uitvoeren").
 * Bestaande snippets met dezelfde naam worden bijgewerkt.
 * Draait via setup.sh:  wp eval-file /scripts/snippets-import.php
 */

if ( ! function_exists( '\Code_Snippets\save_snippet' ) ) {
	WP_CLI::warning( 'Code Snippets is niet actief; snippets overgeslagen.' );
	return;
}

$names = [
	'factuur-opmaak'   => 'Sampark — factuur en pakbon: regelgegevens',
	'donatie-prijs'    => 'Sampark — donatiebedrag als prijs',
	'sponsor-betaling' => 'Sampark — deelname via sponsorpakket (vervangt Woo Discount Rules)',
];

$existing = [];
if ( ! defined( 'CODE_SNIPPETS_SAFE_MODE' ) || ! CODE_SNIPPETS_SAFE_MODE ) {
	WP_CLI::warning( 'Draai dit script met --exec="define(\'CODE_SNIPPETS_SAFE_MODE\', true);", anders kan activeren mislukken.' );
}
foreach ( \Code_Snippets\get_snippets() as $s ) {
	$existing[ $s->name ] = $s;
}

foreach ( glob( '/snippets/*.php' ) as $file ) {
	$key  = basename( $file, '.php' );
	$code = trim( preg_replace( '/^<\?php\s*/', '', file_get_contents( $file ) ) );
	$name = $names[ $key ] ?? $key;

	$snippet = $existing[ $name ] ?? new \Code_Snippets\Model\Snippet();
	$snippet->name   = $name;
	$snippet->code   = $code;
	$snippet->scope  = 'global';
	$snippet->active = true;
	$snippet->tags   = [ 'sampark' ];
	if ( preg_match( '#^/\*\*(.*?)\*/#s', $code, $m ) ) {
		$snippet->desc = trim( preg_replace( '/^\s*\* ?/m', '', $m[1] ) );
	}

	$saved = \Code_Snippets\save_snippet( $snippet );
	// Code Snippets zet een snippet na wijzigen uit; daarom expliciet (opnieuw) activeren. De validatie daarbij
	// faalt als de snippets al geladen zijn ("function already declared"): draai dit script daarom in safe mode.
	if ( $saved && ! \Code_Snippets\get_snippet( $saved->id )->active ) {
		$result = \Code_Snippets\activate_snippet( $saved->id );
		if ( is_string( $result ) ) {
			WP_CLI::warning( "$name: $result" );
		}
	}
	WP_CLI::log( sprintf( '  %s snippet %s (%s)', isset( $existing[ $name ] ) ? '~' : '+', $name, $saved ? $saved->id : 'mislukt' ) );
}
