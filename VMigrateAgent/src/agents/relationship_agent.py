"""
Relationship Agent for mapping foreign keys and table relationships.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.engine import Engine

from ..models.schema import Table, ForeignKey, DatabaseType
from .base_agent import BaseAgent

class RelationshipAgent(BaseAgent):
    """
    Agent responsible for mapping foreign keys and table relationships.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the relationship agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("Relationship", config)
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relationships from the database.
        
        Args:
            data: Dictionary containing:
                - engine: SQLAlchemy engine
                - database_type: DatabaseType enum
                - tables: Dictionary of Table objects
                
        Returns:
            Dictionary with updated tables containing relationship information
        """
        engine = data.get("engine")
        if not engine:
            raise ValueError("Engine is required")
            
        database_type = data.get("database_type")
        if not database_type:
            raise ValueError("Database type is required")
            
        tables = data.get("tables")
        if not tables:
            raise ValueError("Tables are required")
            
        self.logger.info(f"Extracting relationships from {database_type} database")
        
        # Extract foreign keys for each table
        updated_tables = await self._extract_relationships(engine, database_type, tables)
        
        self.logger.info(f"Extracted relationships for {len(updated_tables)} tables")
        
        return {
            "tables": updated_tables
        }
    
    async def _extract_relationships(self, engine: Engine, db_type: DatabaseType, 
                                   tables: Dict[str, Table]) -> Dict[str, Table]:
        """
        Extract foreign key relationships for all tables.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            tables: Dictionary of Table objects
            
        Returns:
            Updated dictionary of Table objects with relationship information
        """
        loop = asyncio.get_event_loop()
        inspector = inspect(engine)
        
        # Process each table
        for table_key, table in tables.items():
            try:
                # Get foreign keys
                fk_info = await loop.run_in_executor(
                    None, 
                    lambda: inspector.get_foreign_keys(table.name, schema=table.schema)
                )
                
                # Process each foreign key
                for fk in fk_info:
                    # Create ForeignKey object
                    foreign_key = ForeignKey(
                        name=fk.get('name', f"fk_{table.name}_{fk['referred_table']}"),
                        table_name=table.name,
                        column_name=fk['constrained_columns'][0] if fk['constrained_columns'] else "",
                        referenced_table_name=fk['referred_table'],
                        referenced_column_name=fk['referred_columns'][0] if fk['referred_columns'] else "",
                        update_rule=fk.get('options', {}).get('onupdate', 'NO ACTION'),
                        delete_rule=fk.get('options', {}).get('ondelete', 'NO ACTION')
                    )
                    
                    # Add to table
                    table.foreign_keys.append(foreign_key)
                    
            except Exception as e:
                self.logger.error(f"Error extracting relationships for table {table_key}: {str(e)}")
                
        return tables
    
    async def _extract_indexes(self, engine: Engine, db_type: DatabaseType, 
                             tables: Dict[str, Table]) -> Dict[str, Table]:
        """
        Extract indexes for all tables.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            tables: Dictionary of Table objects
            
        Returns:
            Updated dictionary of Table objects with index information
        """
        loop = asyncio.get_event_loop()
        inspector = inspect(engine)
        
        # Process each table
        for table_key, table in tables.items():
            try:
                # Get indexes
                idx_info = await loop.run_in_executor(
                    None, 
                    lambda: inspector.get_indexes(table.name, schema=table.schema)
                )
                
                # Get primary key info
                pk_info = await loop.run_in_executor(
                    None, 
                    lambda: inspector.get_pk_constraint(table.name, schema=table.schema)
                )
                
                # Add primary key as an index if it exists
                if pk_info and 'constrained_columns' in pk_info and pk_info['constrained_columns']:
                    from ..models.schema import Index
                    pk_index = Index(
                        name=pk_info.get('name', f"pk_{table.name}"),
                        table_name=table.name,
                        column_names=pk_info['constrained_columns'],
                        is_unique=True,
                        is_primary=True
                    )
                    table.indexes.append(pk_index)
                
                # Process each index
                for idx in idx_info:
                    from ..models.schema import Index
                    index = Index(
                        name=idx.get('name', f"idx_{table.name}_{idx['column_names'][0]}"),
                        table_name=table.name,
                        column_names=idx['column_names'],
                        is_unique=idx.get('unique', False),
                        is_primary=False
                    )
                    table.indexes.append(index)
                    
            except Exception as e:
                self.logger.error(f"Error extracting indexes for table {table_key}: {str(e)}")
                
        return tables
