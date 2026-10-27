<?php
/**
 * Plugin Name: Local Mailpit
 * Description: Stuurt alle mail lokaal naar Mailpit (http://localhost:8025).
 */

if ( wp_get_environment_type() !== 'local' ) {
	return;
}

add_action( 'phpmailer_init', function ( $phpmailer ) {
	$phpmailer->isSMTP();
	$phpmailer->Host     = 'mailpit';
	$phpmailer->Port     = 1025;
	$phpmailer->SMTPAuth = false;
} );
