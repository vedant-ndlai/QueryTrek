"""
Table Agent for extracting table definitions and columns.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.engine import Engine

from ..models.schema import Table, Column, DatabaseType
from .base_agent import BaseAgent

class TableAgent(BaseAgent):
    """
    Agent responsible for extracting table definitions and columns.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the table agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("Table", config)
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tables from the database.
        
        Args:
            data: Dictionary containing:
                - engine: SQLAlchemy engine
                - database_type: DatabaseType enum
                - database_name: Name of the database
                - schema_filter: Optional list of schemas to include
                
        Returns:
            Dictionary with extracted tables
        """
        engine = data.get("engine")
        if not engine:
            raise ValueError("Engine is required")
            
        database_type = data.get("database_type")
        if not database_type:
            raise ValueError("Database type is required")
            
        database_name = data.get("database_name")
        schema_filter = data.get("schema_filter")
        
        self.logger.info(f"Extracting tables from {database_type} database: {database_name}")
        
        # Extract tables based on database type
        tables = await self._extract_tables(engine, database_type, schema_filter)
        
        self.logger.info(f"Extracted {len(tables)} tables")
        
        return {
            "tables": tables
        }
    
    async def _extract_tables(self, engine: Engine, db_type: DatabaseType, 
                             schema_filter: Optional[List[str]] = None) -> Dict[str, Table]:
        """
        Extract tables from the database.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            schema_filter: Optional list of schemas to include
            
        Returns:
            Dictionary of extracted tables
        """
        tables = {}
        
        # Get schemas
        schemas = await self._get_schemas(engine, db_type)
        
        # Filter schemas if needed
        if schema_filter:
            schemas = [s for s in schemas if s in schema_filter]
            
        # Process each schema
        for schema in schemas:
            schema_tables = await self._extract_schema_tables(engine, db_type, schema)
            tables.update(schema_tables)
            
        return tables
    
    async def _get_schemas(self, engine: Engine, db_type: DatabaseType) -> List[str]:
        """
        Get list of schemas in the database.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            
        Returns:
            List of schema names
        """
        loop = asyncio.get_event_loop()
        
        try:
            inspector = inspect(engine)
            
            if db_type == DatabaseType.POSTGRESQL:
                # For PostgreSQL, get all non-system schemas
                schemas = await loop.run_in_executor(None, lambda: inspector.get_schema_names())
                return [s for s in schemas if s not in ('information_schema', 'pg_catalog', 'pg_toast')]
                
            elif db_type == DatabaseType.MYSQL:
                # MySQL doesn't have schemas in the same way, use database name
                return [engine.url.database]
                
            elif db_type == DatabaseType.SQLSERVER:
                # For SQL Server, get all non-system schemas
                schemas = await loop.run_in_executor(None, lambda: inspector.get_schema_names())
                return [s for s in schemas if s not in ('INFORMATION_SCHEMA', 'sys', 'guest')]
                
            elif db_type == DatabaseType.SYBASE:
                # For Sybase, similar to SQL Server
                schemas = await loop.run_in_executor(None, lambda: inspector.get_schema_names())
                return [s for s in schemas if s not in ('INFORMATION_SCHEMA', 'sys', 'guest')]
                
            else:
                # Default behavior
                return await loop.run_in_executor(None, lambda: inspector.get_schema_names())
                
        except Exception as e:
            self.logger.error(f"Error getting schemas: {str(e)}")
            # Default to public schema
            return ['public']
    
    async def _extract_schema_tables(self, engine: Engine, db_type: DatabaseType, 
                                    schema: str) -> Dict[str, Table]:
        """
        Extract tables from a specific schema.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            schema: Schema name
            
        Returns:
            Dictionary of extracted tables
        """
        tables = {}
        loop = asyncio.get_event_loop()
        
        try:
            inspector = inspect(engine)
            
            # Get table names in the schema
            table_names = await loop.run_in_executor(None, lambda: inspector.get_table_names(schema=schema))
            
            # Process each table
            for table_name in table_names:
                table = await self._extract_table(engine, db_type, schema, table_name)
                tables[f"{schema}.{table_name}"] = table
                
            return tables
            
        except Exception as e:
            self.logger.error(f"Error extracting tables from schema {schema}: {str(e)}")
            return {}
    
    async def _extract_table(self, engine: Engine, db_type: DatabaseType, 
                            schema: str, table_name: str) -> Table:
        """
        Extract a single table definition.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            schema: Schema name
            table_name: Table name
            
        Returns:
            Table model
        """
        loop = asyncio.get_event_loop()
        inspector = inspect(engine)
        
        # Create table model
        table = Table(name=table_name, schema=schema)
        
        # Get columns
        columns_info = await loop.run_in_executor(None, lambda: inspector.get_columns(table_name, schema=schema))
        primary_key_columns = await loop.run_in_executor(None, lambda: inspector.get_pk_constraint(table_name, schema=schema))
        primary_keys = primary_key_columns.get('constrained_columns', [])
        
        # Process columns
        for col_idx, col_info in enumerate(columns_info):
            column = Column(
                name=col_info['name'],
                data_type=str(col_info['type']),
                is_nullable=col_info.get('nullable', True),
                default_value=str(col_info.get('default', '')) if col_info.get('default') is not None else None,
                is_primary_key=col_info['name'] in primary_keys,
                character_maximum_length=getattr(col_info.get('type'), 'length', None),
                ordinal_position=col_idx + 1
            )
            table.columns.append(column)
            
        # Set primary key
        if primary_keys:
            table.primary_key = primary_keys
            
        # Get table comment if available
        try:
            if db_type == DatabaseType.POSTGRESQL:
                with engine.connect() as conn:
                    query = text("""
                        SELECT obj_description(pg_class.oid) as comment
                        FROM pg_class
                        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
                        WHERE pg_class.relname = :table_name AND pg_namespace.nspname = :schema
                    """)
                    result = conn.execute(query, {"table_name": table_name, "schema": schema}).scalar()
                    table.comment = result
            elif db_type == DatabaseType.MYSQL:
                with engine.connect() as conn:
                    query = text("""
                        SELECT table_comment
                        FROM information_schema.tables
                        WHERE table_schema = :schema AND table_name = :table_name
                    """)
                    result = conn.execute(query, {"table_name": table_name, "schema": schema}).scalar()
                    table.comment = result
        except Exception as e:
            self.logger.warning(f"Could not get comment for table {schema}.{table_name}: {str(e)}")
            
        return table
