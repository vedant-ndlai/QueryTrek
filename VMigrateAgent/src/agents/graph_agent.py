"""
Graph Agent for storing schema data in a Neo4j graph database.
"""
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from neo4j import GraphDatabase, AsyncGraphDatabase

from ..models.schema import (
    DatabaseSchema, 
    DatabaseType, 
    Table, 
    Column, 
    ForeignKey, 
    StoredProcedure, 
    View, 
    Trigger, 
    Dependency
)
from .base_agent import BaseAgent

class GraphAgent(BaseAgent):
    """
    Agent responsible for storing schema data in a Neo4j graph database.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the graph agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("Graph", config)
        self.uri = config.get("neo4j_uri", "bolt://localhost:7687") if config else "bolt://localhost:7687"
        self.username = config.get("neo4j_username", "neo4j") if config else "neo4j"
        self.password = config.get("neo4j_password", "password") if config else "password"
        self.driver = None
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store schema data in Neo4j graph database.
        
        Args:
            data: Dictionary containing:
                - schema: DatabaseSchema object
                - database_name: Name of the database
                - database_type: DatabaseType enum
                
        Returns:
            Dictionary with status information
        """
        schema = data.get("schema")
        if not schema:
            raise ValueError("Schema is required")
            
        database_name = data.get("database_name")
        if not database_name:
            raise ValueError("Database name is required")
            
        database_type = data.get("database_type")
        if not database_type:
            raise ValueError("Database type is required")
            
        self.logger.info(f"Storing schema for {database_name} in Neo4j")
        
        # Connect to Neo4j
        await self._connect()
        
        # Store schema data
        await self._store_schema(schema, database_name, database_type)
        
        # Close connection
        await self._close()
        
        return {
            "status": "success",
            "message": f"Schema for {database_name} stored in Neo4j"
        }
    
    async def _connect(self) -> None:
        """
        Connect to Neo4j database.
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self.logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
    
    async def _close(self) -> None:
        """
        Close Neo4j connection.
        """
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")
    
    async def _store_schema(self, schema: DatabaseSchema, database_name: str, 
                          database_type: DatabaseType) -> None:
        """
        Store schema data in Neo4j.
        
        Args:
            schema: DatabaseSchema object
            database_name: Name of the database
            database_type: DatabaseType enum
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Create database node
            await loop.run_in_executor(None, lambda: self._create_database_node(database_name, database_type))
            
            # Store tables
            for table in schema.tables.values():
                await loop.run_in_executor(None, lambda: self._store_table(table, database_name))
            
            # Store procedures
            for procedure in schema.procedures.values():
                await loop.run_in_executor(None, lambda: self._store_procedure(procedure, database_name))
            
            # Store views
            for view in schema.views.values():
                await loop.run_in_executor(None, lambda: self._store_view(view, database_name))
            
            # Store dependencies
            for dependency in schema.dependencies:
                await loop.run_in_executor(None, lambda: self._store_dependency(dependency, database_name))
                
            self.logger.info(f"Schema for {database_name} stored in Neo4j")
            
        except Exception as e:
            self.logger.error(f"Error storing schema in Neo4j: {str(e)}")
            raise
    
    def _create_database_node(self, database_name: str, database_type: DatabaseType) -> None:
        """
        Create database node in Neo4j.
        
        Args:
            database_name: Name of the database
            database_type: DatabaseType enum
        """
        with self.driver.session() as session:
            # Create database node
            session.run(
                """
                MERGE (db:Database {name: $name, type: $type})
                """,
                name=database_name,
                type=database_type.value
            )
    
    def _store_table(self, table: Table, database_name: str) -> None:
        """
        Store table in Neo4j.
        
        Args:
            table: Table object
            database_name: Name of the database
        """
        with self.driver.session() as session:
            # Create table node
            session.run(
                """
                MATCH (db:Database {name: $database_name})
                MERGE (t:Table {name: $name, schema: $schema, full_name: $full_name})
                MERGE (t)-[:BELONGS_TO]->(db)
                """,
                database_name=database_name,
                name=table.name,
                schema=table.schema,
                full_name=f"{table.schema}.{table.name}"
            )
            
            # Create column nodes
            for column in table.columns:
                session.run(
                    """
                    MATCH (t:Table {full_name: $table_full_name})
                    MERGE (c:Column {
                        name: $name, 
                        data_type: $data_type, 
                        is_nullable: $is_nullable,
                        is_primary_key: $is_primary_key,
                        ordinal_position: $ordinal_position,
                        full_name: $full_name
                    })
                    MERGE (c)-[:BELONGS_TO]->(t)
                    """,
                    table_full_name=f"{table.schema}.{table.name}",
                    name=column.name,
                    data_type=column.data_type,
                    is_nullable=column.is_nullable,
                    is_primary_key=column.is_primary_key,
                    ordinal_position=column.ordinal_position,
                    full_name=f"{table.schema}.{table.name}.{column.name}"
                )
            
            # Create foreign key relationships
            for fk in table.foreign_keys:
                session.run(
                    """
                    MATCH (source_table:Table {full_name: $source_table_name})
                    MATCH (source_column:Column {full_name: $source_column_name})
                    MATCH (target_table:Table {full_name: $target_table_name})
                    MATCH (target_column:Column {full_name: $target_column_name})
                    MERGE (source_column)-[r:REFERENCES {
                        name: $name,
                        update_rule: $update_rule,
                        delete_rule: $delete_rule
                    }]->(target_column)
                    """,
                    source_table_name=f"{table.schema}.{fk.table_name}",
                    source_column_name=f"{table.schema}.{fk.table_name}.{fk.column_name}",
                    target_table_name=f"{table.schema}.{fk.referenced_table_name}",
                    target_column_name=f"{table.schema}.{fk.referenced_table_name}.{fk.referenced_column_name}",
                    name=fk.name,
                    update_rule=fk.update_rule,
                    delete_rule=fk.delete_rule
                )
    
    def _store_procedure(self, procedure: StoredProcedure, database_name: str) -> None:
        """
        Store procedure in Neo4j.
        
        Args:
            procedure: StoredProcedure object
            database_name: Name of the database
        """
        with self.driver.session() as session:
            # Create procedure node
            session.run(
                """
                MATCH (db:Database {name: $database_name})
                MERGE (p:Procedure {
                    name: $name, 
                    schema: $schema, 
                    type: $type,
                    return_type: $return_type,
                    full_name: $full_name
                })
                MERGE (p)-[:BELONGS_TO]->(db)
                """,
                database_name=database_name,
                name=procedure.name,
                schema=procedure.schema,
                type=procedure.type,
                return_type=procedure.return_type,
                full_name=f"{procedure.schema}.{procedure.name}"
            )
            
            # Create parameter nodes
            for i, param in enumerate(procedure.parameters):
                session.run(
                    """
                    MATCH (p:Procedure {full_name: $proc_full_name})
                    MERGE (param:Parameter {
                        name: $name, 
                        type: $type, 
                        position: $position,
                        full_name: $full_name
                    })
                    MERGE (param)-[:BELONGS_TO]->(p)
                    """,
                    proc_full_name=f"{procedure.schema}.{procedure.name}",
                    name=param.get('name', f"param{i}"),
                    type=param.get('type', 'unknown'),
                    position=param.get('position', i),
                    full_name=f"{procedure.schema}.{procedure.name}.{param.get('name', f'param{i}')}"
                )
    
    def _store_view(self, view: View, database_name: str) -> None:
        """
        Store view in Neo4j.
        
        Args:
            view: View object
            database_name: Name of the database
        """
        with self.driver.session() as session:
            # Create view node
            session.run(
                """
                MATCH (db:Database {name: $database_name})
                MERGE (v:View {
                    name: $name, 
                    schema: $schema, 
                    full_name: $full_name
                })
                MERGE (v)-[:BELONGS_TO]->(db)
                """,
                database_name=database_name,
                name=view.name,
                schema=view.schema,
                full_name=f"{view.schema}.{view.name}"
            )
            
            # Create column nodes
            for column in view.columns:
                session.run(
                    """
                    MATCH (v:View {full_name: $view_full_name})
                    MERGE (c:Column {
                        name: $name, 
                        data_type: $data_type, 
                        is_nullable: $is_nullable,
                        ordinal_position: $ordinal_position,
                        full_name: $full_name
                    })
                    MERGE (c)-[:BELONGS_TO]->(v)
                    """,
                    view_full_name=f"{view.schema}.{view.name}",
                    name=column.name,
                    data_type=column.data_type,
                    is_nullable=column.is_nullable,
                    ordinal_position=column.ordinal_position,
                    full_name=f"{view.schema}.{view.name}.{column.name}"
                )
    
    def _store_dependency(self, dependency: Dependency, database_name: str) -> None:
        """
        Store dependency in Neo4j.
        
        Args:
            dependency: Dependency object
            database_name: Name of the database
        """
        with self.driver.session() as session:
            # Map source type to node label
            source_label = self._map_type_to_label(dependency.source_type)
            target_label = self._map_type_to_label(dependency.target_type)
            
            # Create dependency relationship
            session.run(
                f"""
                MATCH (source:{source_label} {{
                    schema: $source_schema, 
                    name: $source_name
                }})
                MATCH (target:{target_label} {{
                    schema: $target_schema, 
                    name: $target_name
                }})
                MERGE (source)-[r:DEPENDS_ON {{
                    type: $dependency_type
                }}]->(target)
                """,
                source_schema=dependency.source_schema,
                source_name=dependency.source_name,
                target_schema=dependency.target_schema,
                target_name=dependency.target_name,
                dependency_type=dependency.dependency_type
            )
    
    def _map_type_to_label(self, type_str: str) -> str:
        """
        Map type string to Neo4j node label.
        
        Args:
            type_str: Type string
            
        Returns:
            Neo4j node label
        """
        type_map = {
            "TABLE": "Table",
            "VIEW": "View",
            "PROCEDURE": "Procedure",
            "FUNCTION": "Procedure",  # Functions are stored as procedures with type='FUNCTION'
            "TRIGGER": "Trigger"
        }
        
        return type_map.get(type_str, "Unknown")
    
    async def export_to_json(self, schema: DatabaseSchema, output_path: str) -> None:
        """
        Export schema to JSON file.
        
        Args:
            schema: DatabaseSchema object
            output_path: Path to output JSON file
        """
        try:
            # Convert schema to dictionary
            schema_dict = schema.dict()
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(schema_dict, f, indent=2)
                
            self.logger.info(f"Schema exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting schema to JSON: {str(e)}")
            raise
