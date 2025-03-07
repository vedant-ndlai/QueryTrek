"""
Visualizer for generating interactive dependency charts.
"""
import json
import logging
import os
import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
import d3graph

from ..models.schema import DatabaseSchema, Dependency

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class SchemaVisualizer:
    """
    Visualizer for generating interactive dependency charts.
    """
    
    def __init__(self):
        """
        Initialize the schema visualizer.
        """
        self.logger = logging.getLogger("SchemaVisualizer")
        
    def generate_dependency_graph(self, schema: DatabaseSchema, output_dir: str) -> str:
        """
        Generate dependency graph visualization.
        
        Args:
            schema: DatabaseSchema object
            output_dir: Output directory for visualization files
            
        Returns:
            Path to HTML file
        """
        try:
            self.logger.info(f"Generating dependency graph for {schema.database_name}")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Create NetworkX graph
            G = self._create_graph(schema)
            
            # Generate visualization using d3graph
            html_path = self._generate_d3_visualization(G, schema.database_name, output_dir)
            
            self.logger.info(f"Dependency graph generated: {html_path}")
            
            return html_path
            
        except Exception as e:
            self.logger.error(f"Error generating dependency graph: {str(e)}")
            raise
    
    def _create_graph(self, schema: DatabaseSchema) -> nx.DiGraph:
        """
        Create NetworkX graph from schema.
        
        Args:
            schema: DatabaseSchema object
            
        Returns:
            NetworkX DiGraph
        """
        # Create directed graph
        G = nx.DiGraph()
        
        # Add table nodes
        for table_key, table in schema.tables.items():
            G.add_node(
                table_key,
                label=table.name,
                type='table',
                schema=table.schema,
                columns=len(table.columns)
            )
        
        # Add procedure nodes
        for proc_key, proc in schema.procedures.items():
            G.add_node(
                proc_key,
                label=proc.name,
                type='procedure',
                schema=proc.schema,
                proc_type=proc.type
            )
        
        # Add view nodes
        for view_key, view in schema.views.items():
            G.add_node(
                view_key,
                label=view.name,
                type='view',
                schema=view.schema
            )
        
        # Add dependency edges
        for dep in schema.dependencies:
            source_key = f"{dep.source_schema}.{dep.source_name}"
            target_key = f"{dep.target_schema}.{dep.target_name}"
            
            # Check if nodes exist
            if source_key in G and target_key in G:
                G.add_edge(
                    source_key,
                    target_key,
                    type=dep.dependency_type
                )
        
        return G
    
    def _generate_d3_visualization(self, G: nx.DiGraph, database_name: str, output_dir: str) -> str:
        """
        Generate D3.js visualization.
        
        Args:
            G: NetworkX DiGraph
            database_name: Name of the database
            output_dir: Output directory
            
        Returns:
            Path to HTML file
        """
        # Create output path
        output_path = os.path.join(output_dir, f"{database_name}_dependency_graph.html")
        
        # Create node colors based on type
        node_colors = []
        for node in G.nodes():
            node_type = G.nodes[node].get('type', 'unknown')
            if node_type == 'table':
                node_colors.append('#4285F4')  # Blue for tables
            elif node_type == 'procedure':
                node_colors.append('#EA4335')  # Red for procedures
            elif node_type == 'view':
                node_colors.append('#FBBC05')  # Yellow for views
            else:
                node_colors.append('#34A853')  # Green for others
        
        # Create edge colors based on type
        edge_colors = []
        for source, target in G.edges():
            edge_type = G.edges[(source, target)].get('type', 'unknown')
            if edge_type == 'REFERENCES':
                edge_colors.append('#4285F4')  # Blue for references
            elif edge_type == 'USES':
                edge_colors.append('#EA4335')  # Red for uses
            elif edge_type == 'CALLS':
                edge_colors.append('#FBBC05')  # Yellow for calls
            else:
                edge_colors.append('#34A853')  # Green for others
        
        # Create d3graph
        d3 = d3graph.d3graph()
        
        # Add nodes
        for node in G.nodes():
            node_attrs = G.nodes[node]
            d3.add_node(
                node,
                label=node_attrs.get('label', node),
                title=f"{node_attrs.get('type', 'unknown')}: {node}",
                size=10,
                color=node_colors[list(G.nodes()).index(node)]
            )
        
        # Add edges
        for i, (source, target) in enumerate(G.edges()):
            edge_attrs = G.edges[(source, target)]
            d3.add_edge(
                source,
                target,
                weight=1,
                label=edge_attrs.get('type', ''),
                color=edge_colors[i]
            )
        
        # Set graph properties
        d3.set_node_properties(
            hover_tooltip=True,
            collision_scale=0.5
        )
        
        d3.set_edge_properties(
            directed=True,
            edge_distance=100
        )
        
        # Set graph title
        d3.set_title(f"Dependency Graph for {database_name}")
        
        # Add legend
        d3.add_legend(
            {
                'Table': '#4285F4',
                'Procedure': '#EA4335',
                'View': '#FBBC05',
                'Other': '#34A853'
            },
            title='Node Types'
        )
        
        # Save to HTML
        d3.save(output_path)
        
        return output_path
    
    def generate_json_representation(self, schema: DatabaseSchema, output_path: str) -> str:
        """
        Generate JSON representation of schema.
        
        Args:
            schema: DatabaseSchema object
            output_path: Path to output JSON file
            
        Returns:
            Path to JSON file
        """
        try:
            self.logger.info(f"Generating JSON representation for {schema.database_name}")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Convert schema to dictionary
            schema_dict = {
                "database_name": schema.database_name,
                "database_type": schema.database_type.value,
                "tables": [],
                "procedures": [],
                "views": [],
                "dependencies": []
            }
            
            # Add tables
            for table_key, table in schema.tables.items():
                table_dict = {
                    "name": table.name,
                    "schema": table.schema,
                    "columns": [
                        {
                            "name": col.name,
                            "data_type": col.data_type,
                            "is_nullable": col.is_nullable,
                            "is_primary_key": col.is_primary_key,
                            "ordinal_position": col.ordinal_position
                        }
                        for col in table.columns
                    ],
                    "foreign_keys": [
                        {
                            "name": fk.name,
                            "column_name": fk.column_name,
                            "referenced_table_name": fk.referenced_table_name,
                            "referenced_column_name": fk.referenced_column_name,
                            "update_rule": fk.update_rule,
                            "delete_rule": fk.delete_rule
                        }
                        for fk in table.foreign_keys
                    ]
                }
                schema_dict["tables"].append(table_dict)
            
            # Add procedures
            for proc_key, proc in schema.procedures.items():
                proc_dict = {
                    "name": proc.name,
                    "schema": proc.schema,
                    "type": proc.type,
                    "parameters": proc.parameters,
                    "return_type": proc.return_type
                }
                schema_dict["procedures"].append(proc_dict)
            
            # Add views
            for view_key, view in schema.views.items():
                view_dict = {
                    "name": view.name,
                    "schema": view.schema,
                    "columns": [
                        {
                            "name": col.name,
                            "data_type": col.data_type,
                            "is_nullable": col.is_nullable,
                            "ordinal_position": col.ordinal_position
                        }
                        for col in view.columns
                    ]
                }
                schema_dict["views"].append(view_dict)
            
            # Add dependencies
            for dep in schema.dependencies:
                dep_dict = {
                    "source_type": dep.source_type,
                    "source_name": dep.source_name,
                    "source_schema": dep.source_schema,
                    "target_type": dep.target_type,
                    "target_name": dep.target_name,
                    "target_schema": dep.target_schema,
                    "dependency_type": dep.dependency_type
                }
                schema_dict["dependencies"].append(dep_dict)
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(schema_dict, f, indent=2)
                
            self.logger.info(f"JSON representation generated: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating JSON representation: {str(e)}")
            raise
