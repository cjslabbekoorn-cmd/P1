<?php
/**
 * Exporteert de Sampark-inrichting van JetEngine als "skin" (JetEngine › Dashboard › Skins › Import).
 * Draait via:  docker compose run --rm wpcli eval-file /scripts/jetengine-export.php
 * Schrijft naar /jetengine/sampark-jetengine.json (map sampark-local/jetengine/).
 */

if ( ! function_exists( 'jet_engine' ) ) {
	WP_CLI::error( 'JetEngine is niet actief.' );
}

require_once jet_engine()->plugin_path( 'includes/dashboard/skins-export.php' );
$export = new Jet_Engine_Skins_Export();
$state  = get_option( 'sampark_jet', [] );

$ids = function ( $type, $slugs ) {
	$out = [];
	foreach ( (array) jet_engine()->db->query( $type, [] ) as $row ) {
		if ( in_array( $row['slug'], $slugs, true ) ) {
			$out[] = $row['id'];
		}
	}
	return $out;
};

$relations = array_column( (array) jet_engine()->relations->data->get_raw(), 'id' );
$options   = array_column( (array) jet_engine()->options_pages->data->get_raw(), 'id' );

$json = [
	'post_types'    => $export->export_post_types( $ids( 'post_types', [ 'projecten', 'evenementen', 'sponsors' ] ) ),
	'taxonomies'    => $export->export_taxonomies( $ids( 'taxonomies', [ 'projecttype', 'regio', 'sponsorniveau' ] ) ),
	'listings'      => $export->export_listings( array_values( $state['listings'] ?? [] ) ),
	'components'    => [],
	'meta_boxes'    => [],
	'relations'     => $export->export_relations( $relations ),
	'options_pages' => $export->export_options_pages( $options ),
	'glossaries'    => $export->export_glossaries( array_values( $state['glossary'] ?? [] ) ),
	'queries'       => $export->export_queries( array_values( $state['queries'] ?? [] ) ),
	'content'       => [],
];

$dir = is_dir( '/jetengine' ) ? '/jetengine' : getcwd();
$file = $dir . '/sampark-jetengine.json';
file_put_contents( $file, wp_json_encode( $json, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) );
WP_CLI::success( sprintf( 'Export geschreven: %s (%d posttypes, %d taxonomieën, %d listings, %d relaties, %d queries)',
	$file, count( $json['post_types'] ), count( $json['taxonomies'] ), count( $json['listings'] ), count( $json['relations'] ), count( $json['queries'] ) ) );
