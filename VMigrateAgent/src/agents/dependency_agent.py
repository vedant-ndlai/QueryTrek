"""
Dependency Agent for analyzing dependencies between database objects.
"""
import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from ..models.schema import (
    DatabaseSchema, 
    DatabaseType, 
    Table, 
    View, 
    StoredProcedure, 
    Trigger, 
    Dependency
)
from .base_agent import BaseAgent

class DependencyAgent(BaseAgent):
    """
    Agent responsible for analyzing dependencies between database objects.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dependency agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("Dependency", config)
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies between database objects.
        
        Args:
            data: Dictionary containing:
                - engine: SQLAlchemy engine
                - database_type: DatabaseType enum
                - database_name: Name of the database
                - schema: DatabaseSchema object containing tables, views, procedures, etc.
                
        Returns:
            Dictionary with updated schema containing dependency information
        """
        engine = data.get("engine")
        if not engine:
            raise ValueError("Engine is required")
            
        database_type = data.get("database_type")
        if not database_type:
            raise ValueError("Database type is required")
            
        database_name = data.get("database_name")
        if not database_name:
            raise ValueError("Database name is required")
            
        schema = data.get("schema")
        if not schema:
            raise ValueError("Schema is required")
            
        self.logger.info(f"Analyzing dependencies in {database_type} database: {database_name}")
        
        # Analyze dependencies based on database type
        updated_schema = await self._analyze_dependencies(engine, database_type, schema)
        
        self.logger.info(f"Analyzed {len(updated_schema.dependencies)} dependencies")
        
        return {
            "schema": updated_schema
        }
    
    async def _analyze_dependencies(self, engine: Engine, db_type: DatabaseType, 
                                  schema: DatabaseSchema) -> DatabaseSchema:
        """
        Analyze dependencies between database objects.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            schema: DatabaseSchema object
            
        Returns:
            Updated DatabaseSchema with dependency information
        """
        # First, analyze foreign key dependencies (table-to-table)
        await self._analyze_foreign_key_dependencies(schema)
        
        # Then, analyze code-based dependencies
        if db_type == DatabaseType.POSTGRESQL:
            await self._analyze_postgresql_dependencies(engine, schema)
        elif db_type == DatabaseType.MYSQL:
            await self._analyze_mysql_dependencies(engine, schema)
        elif db_type == DatabaseType.SQLSERVER:
            await self._analyze_sqlserver_dependencies(engine, schema)
        elif db_type == DatabaseType.SYBASE:
            await self._analyze_sybase_dependencies(engine, schema)
        
        return schema
    
    async def _analyze_foreign_key_dependencies(self, schema: DatabaseSchema) -> None:
        """
        Analyze foreign key dependencies between tables.
        
        Args:
            schema: DatabaseSchema object
        """
        # Process each table
        for table_key, table in schema.tables.items():
            # Process each foreign key
            for fk in table.foreign_keys:
                # Create dependency
                dependency = Dependency(
                    source_type="TABLE",
                    source_name=table.name,
                    source_schema=table.schema,
                    target_type="TABLE",
                    target_name=fk.referenced_table_name,
                    target_schema=table.schema,  # Assuming same schema, adjust if needed
                    dependency_type="REFERENCES"
                )
                
                # Add to schema
                schema.add_dependency(dependency)
    
    async def _analyze_postgresql_dependencies(self, engine: Engine, schema: DatabaseSchema) -> None:
        """
        Analyze dependencies in PostgreSQL.
        
        Args:
            engine: SQLAlchemy engine
            schema: DatabaseSchema object
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Query to get dependencies
            query = text("""
                SELECT 
                    cl.relkind AS source_type,
                    n1.nspname AS source_schema,
                    cl.relname AS source_name,
                    tg.tgname AS trigger_name,
                    d.refclassid::regclass AS target_type_id,
                    n2.nspname AS target_schema,
                    cr.relname AS target_name,
                    d.deptype AS dependency_type
                FROM 
                    pg_depend d
                    JOIN pg_class cl ON cl.oid = d.refobjid
                    JOIN pg_namespace n1 ON n1.oid = cl.relnamespace
                    JOIN pg_class cr ON cr.oid = d.objid
                    JOIN pg_namespace n2 ON n2.oid = cr.relnamespace
                    LEFT JOIN pg_trigger tg ON tg.oid = d.objid
                WHERE 
                    d.deptype IN ('n', 'a')  -- normal dependency, auto dependency
                    AND n1.nspname NOT IN ('pg_catalog', 'information_schema')
                    AND n2.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY 
                    n1.nspname, cl.relname, n2.nspname, cr.relname;
            """)
            
            # Execute query
            with engine.connect() as conn:
                result = await loop.run_in_executor(None, lambda: conn.execute(query))
                rows = await loop.run_in_executor(None, lambda: result.fetchall())
                
                # Process results
                for row in rows:
                    row_dict = dict(row._mapping)
                    
                    # Map source type
                    source_type = "UNKNOWN"
                    if row_dict['source_type'] == 'r':
                        source_type = "TABLE"
                    elif row_dict['source_type'] == 'v':
                        source_type = "VIEW"
                    elif row_dict['source_type'] == 'f':
                        source_type = "FUNCTION"
                    elif row_dict['source_type'] == 'p':
                        source_type = "PROCEDURE"
                    
                    # Map target type (simplified for now)
                    target_type = "UNKNOWN"
                    if "pg_class" in str(row_dict['target_type_id']):
                        target_type = "TABLE"  # Could be table or view
                    elif "pg_proc" in str(row_dict['target_type_id']):
                        target_type = "FUNCTION"  # Could be function or procedure
                    elif "pg_trigger" in str(row_dict['target_type_id']):
                        target_type = "TRIGGER"
                    
                    # Map dependency type
                    dep_type = "USES"
                    if row_dict['dependency_type'] == 'n':
                        dep_type = "USES"
                    elif row_dict['dependency_type'] == 'a':
                        dep_type = "AUTO"
                    
                    # Create dependency
                    dependency = Dependency(
                        source_type=source_type,
                        source_name=row_dict['source_name'],
                        source_schema=row_dict['source_schema'],
                        target_type=target_type,
                        target_name=row_dict['target_name'],
                        target_schema=row_dict['target_schema'],
                        dependency_type=dep_type
                    )
                    
                    # Add to schema
                    schema.add_dependency(dependency)
                    
            # Also analyze dependencies in procedure bodies
            await self._analyze_code_dependencies(schema)
                
        except Exception as e:
            self.logger.error(f"Error analyzing PostgreSQL dependencies: {str(e)}")
    
    async def _analyze_mysql_dependencies(self, engine: Engine, schema: DatabaseSchema) -> None:
        """
        Analyze dependencies in MySQL.
        
        Args:
            engine: SQLAlchemy engine
            schema: DatabaseSchema object
        """
        # MySQL doesn't have a direct way to query dependencies
        # We'll analyze code dependencies instead
        await self._analyze_code_dependencies(schema)
    
    async def _analyze_sqlserver_dependencies(self, engine: Engine, schema: DatabaseSchema) -> None:
        """
        Analyze dependencies in SQL Server.
        
        Args:
            engine: SQLAlchemy engine
            schema: DatabaseSchema object
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Query to get dependencies
            query = text("""
                SELECT 
                    OBJECT_SCHEMA_NAME(referencing_id) AS source_schema,
                    OBJECT_NAME(referencing_id) AS source_name,
                    o1.type_desc AS source_type,
                    OBJECT_SCHEMA_NAME(referenced_id) AS target_schema,
                    OBJECT_NAME(referenced_id) AS target_name,
                    o2.type_desc AS target_type
                FROM 
                    sys.sql_expression_dependencies d
                    JOIN sys.objects o1 ON d.referencing_id = o1.object_id
                    JOIN sys.objects o2 ON d.referenced_id = o2.object_id
                WHERE 
                    is_ambiguous = 0
                ORDER BY 
                    source_schema, source_name, target_schema, target_name;
            """)
            
            # Execute query
            with engine.connect() as conn:
                result = await loop.run_in_executor(None, lambda: conn.execute(query))
                rows = await loop.run_in_executor(None, lambda: result.fetchall())
                
                # Process results
                for row in rows:
                    row_dict = dict(row._mapping)
                    
                    # Map source type
                    source_type = row_dict['source_type']
                    if "TABLE" in source_type:
                        source_type = "TABLE"
                    elif "VIEW" in source_type:
                        source_type = "VIEW"
                    elif "FUNCTION" in source_type:
                        source_type = "FUNCTION"
                    elif "PROCEDURE" in source_type:
                        source_type = "PROCEDURE"
                    elif "TRIGGER" in source_type:
                        source_type = "TRIGGER"
                    else:
                        source_type = "UNKNOWN"
                    
                    # Map target type
                    target_type = row_dict['target_type']
                    if "TABLE" in target_type:
                        target_type = "TABLE"
                    elif "VIEW" in target_type:
                        target_type = "VIEW"
                    elif "FUNCTION" in target_type:
                        target_type = "FUNCTION"
                    elif "PROCEDURE" in target_type:
                        target_type = "PROCEDURE"
                    elif "TRIGGER" in target_type:
                        target_type = "TRIGGER"
                    else:
                        target_type = "UNKNOWN"
                    
                    # Create dependency
                    dependency = Dependency(
                        source_type=source_type,
                        source_name=row_dict['source_name'],
                        source_schema=row_dict['source_schema'],
                        target_type=target_type,
                        target_name=row_dict['target_name'],
                        target_schema=row_dict['target_schema'],
                        dependency_type="USES"
                    )
                    
                    # Add to schema
                    schema.add_dependency(dependency)
                    
            # Also analyze dependencies in procedure bodies
            await self._analyze_code_dependencies(schema)
                
        except Exception as e:
            self.logger.error(f"Error analyzing SQL Server dependencies: {str(e)}")
    
    async def _analyze_sybase_dependencies(self, engine: Engine, schema: DatabaseSchema) -> None:
        """
        Analyze dependencies in Sybase.
        
        Args:
            engine: SQLAlchemy engine
            schema: DatabaseSchema object
        """
        # Sybase doesn't have a direct way to query dependencies
        # We'll analyze code dependencies instead
        await self._analyze_code_dependencies(schema)
    
    async def _analyze_code_dependencies(self, schema: DatabaseSchema) -> None:
        """
        Analyze dependencies in stored procedure and function code.
        
        Args:
            schema: DatabaseSchema object
        """
        # Get all object names for pattern matching
        table_names = self._get_object_names(schema.tables)
        view_names = self._get_object_names(schema.views)
        procedure_names = self._get_object_names(schema.procedures)
        
        # Process each procedure
        for proc_key, proc in schema.procedures.items():
            # Skip if no body
            if not proc.body:
                continue
                
            # Find table references
            table_refs = self._find_references(proc.body, table_names)
            for table_ref in table_refs:
                # Extract schema and name
                parts = table_ref.split('.')
                if len(parts) == 2:
                    target_schema, target_name = parts
                else:
                    target_schema = proc.schema  # Assume same schema
                    target_name = table_ref
                    
                # Create dependency
                dependency = Dependency(
                    source_type="PROCEDURE" if proc.type == "PROCEDURE" else "FUNCTION",
                    source_name=proc.name,
                    source_schema=proc.schema,
                    target_type="TABLE",
                    target_name=target_name,
                    target_schema=target_schema,
                    dependency_type="USES"
                )
                
                # Add to schema
                schema.add_dependency(dependency)
                
            # Find view references
            view_refs = self._find_references(proc.body, view_names)
            for view_ref in view_refs:
                # Extract schema and name
                parts = view_ref.split('.')
                if len(parts) == 2:
                    target_schema, target_name = parts
                else:
                    target_schema = proc.schema  # Assume same schema
                    target_name = view_ref
                    
                # Create dependency
                dependency = Dependency(
                    source_type="PROCEDURE" if proc.type == "PROCEDURE" else "FUNCTION",
                    source_name=proc.name,
                    source_schema=proc.schema,
                    target_type="VIEW",
                    target_name=target_name,
                    target_schema=target_schema,
                    dependency_type="USES"
                )
                
                # Add to schema
                schema.add_dependency(dependency)
                
            # Find procedure references
            proc_refs = self._find_references(proc.body, procedure_names)
            for proc_ref in proc_refs:
                # Skip self-references
                if proc_ref == f"{proc.schema}.{proc.name}" or proc_ref == proc.name:
                    continue
                    
                # Extract schema and name
                parts = proc_ref.split('.')
                if len(parts) == 2:
                    target_schema, target_name = parts
                else:
                    target_schema = proc.schema  # Assume same schema
                    target_name = proc_ref
                    
                # Create dependency
                dependency = Dependency(
                    source_type="PROCEDURE" if proc.type == "PROCEDURE" else "FUNCTION",
                    source_name=proc.name,
                    source_schema=proc.schema,
                    target_type="PROCEDURE",  # Assuming procedure, could be function
                    target_name=target_name,
                    target_schema=target_schema,
                    dependency_type="CALLS"
                )
                
                # Add to schema
                schema.add_dependency(dependency)
    
    def _get_object_names(self, objects: Dict[str, Any]) -> List[str]:
        """
        Get list of object names for pattern matching.
        
        Args:
            objects: Dictionary of objects
            
        Returns:
            List of object names
        """
        names = []
        
        # Add fully qualified names
        for key in objects.keys():
            names.append(key)
            
        # Add short names
        for obj in objects.values():
            names.append(obj.name)
            
        return names
    
    def _find_references(self, code: str, object_names: List[str]) -> Set[str]:
        """
        Find references to objects in code.
        
        Args:
            code: SQL code to analyze
            object_names: List of object names to search for
            
        Returns:
            Set of found references
        """
        references = set()
        
        # Sort by length (longest first) to avoid partial matches
        sorted_names = sorted(object_names, key=len, reverse=True)
        
        # Simple pattern matching
        for name in sorted_names:
            # Escape special characters
            escaped_name = re.escape(name)
            
            # Pattern to match name with word boundaries
            pattern = r'\b' + escaped_name + r'\b'
            
            # Find all matches
            matches = re.findall(pattern, code, re.IGNORECASE)
            
            # Add to references
            for match in matches:
                references.add(name)
                
        return references
