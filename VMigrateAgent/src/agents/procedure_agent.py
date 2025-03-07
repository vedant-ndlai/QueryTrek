"""
Procedure Agent for parsing stored procedures and functions.
"""
import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from ..models.schema import StoredProcedure, DatabaseType
from .base_agent import BaseAgent

class ProcedureAgent(BaseAgent):
    """
    Agent responsible for parsing stored procedures and functions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the procedure agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("Procedure", config)
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract stored procedures and functions from the database.
        
        Args:
            data: Dictionary containing:
                - engine: SQLAlchemy engine
                - database_type: DatabaseType enum
                - database_name: Name of the database
                - schema_filter: Optional list of schemas to include
                
        Returns:
            Dictionary with extracted procedures
        """
        engine = data.get("engine")
        if not engine:
            raise ValueError("Engine is required")
            
        database_type = data.get("database_type")
        if not database_type:
            raise ValueError("Database type is required")
            
        database_name = data.get("database_name")
        schema_filter = data.get("schema_filter")
        
        self.logger.info(f"Extracting stored procedures from {database_type} database: {database_name}")
        
        # Extract procedures based on database type
        procedures = await self._extract_procedures(engine, database_type, schema_filter)
        
        self.logger.info(f"Extracted {len(procedures)} stored procedures/functions")
        
        return {
            "procedures": procedures
        }
    
    async def _extract_procedures(self, engine: Engine, db_type: DatabaseType, 
                                schema_filter: Optional[List[str]] = None) -> Dict[str, StoredProcedure]:
        """
        Extract stored procedures and functions from the database.
        
        Args:
            engine: SQLAlchemy engine
            db_type: Database type
            schema_filter: Optional list of schemas to include
            
        Returns:
            Dictionary of extracted procedures
        """
        if db_type == DatabaseType.POSTGRESQL:
            return await self._extract_postgresql_procedures(engine, schema_filter)
        elif db_type == DatabaseType.MYSQL:
            return await self._extract_mysql_procedures(engine, schema_filter)
        elif db_type == DatabaseType.SQLSERVER:
            return await self._extract_sqlserver_procedures(engine, schema_filter)
        elif db_type == DatabaseType.SYBASE:
            return await self._extract_sybase_procedures(engine, schema_filter)
        else:
            self.logger.warning(f"Procedure extraction not implemented for database type: {db_type}")
            return {}
    
    async def _extract_postgresql_procedures(self, engine: Engine, 
                                          schema_filter: Optional[List[str]] = None) -> Dict[str, StoredProcedure]:
        """
        Extract stored procedures and functions from PostgreSQL.
        
        Args:
            engine: SQLAlchemy engine
            schema_filter: Optional list of schemas to include
            
        Returns:
            Dictionary of extracted procedures
        """
        procedures = {}
        loop = asyncio.get_event_loop()
        
        try:
            # Build schema filter condition
            schema_condition = ""
            if schema_filter:
                schema_list = "', '".join(schema_filter)
                schema_condition = f"AND n.nspname IN ('{schema_list}')"
            else:
                schema_condition = "AND n.nspname NOT IN ('pg_catalog', 'information_schema')"
                
            # Query to get procedures and functions
            query = text(f"""
                SELECT 
                    n.nspname AS schema_name,
                    p.proname AS procedure_name,
                    pg_get_function_arguments(p.oid) AS parameters,
                    CASE 
                        WHEN p.prorettype = 'pg_catalog.void'::pg_catalog.regtype THEN 'PROCEDURE'
                        ELSE 'FUNCTION'
                    END AS routine_type,
                    pg_get_function_result(p.oid) AS return_type,
                    pg_get_functiondef(p.oid) AS procedure_body,
                    p.proargtypes AS arg_types,
                    p.prokind AS proc_kind,
                    p.prosrc AS source,
                    p.probin AS external_language,
                    p.provolatile AS volatility,
                    p.proleakproof AS leakproof,
                    p.proisstrict AS strict,
                    p.prosecdef AS security_definer,
                    p.procost AS cost,
                    p.prorows AS rows,
                    p.proconfig AS config,
                    p.proparallel AS parallel,
                    p.pronargs AS num_args,
                    p.pronargdefaults AS num_defaults
                FROM 
                    pg_catalog.pg_proc p
                    LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
                WHERE 
                    p.prokind IN ('f', 'p')
                    {schema_condition}
                ORDER BY 
                    n.nspname, p.proname;
            """)
            
            # Execute query
            with engine.connect() as conn:
                result = await loop.run_in_executor(None, lambda: conn.execute(query))
                rows = await loop.run_in_executor(None, lambda: result.fetchall())
                
                # Process results
                for row in rows:
                    row_dict = dict(row._mapping)
                    
                    # Parse parameters
                    param_list = []
                    if row_dict['parameters']:
                        params = row_dict['parameters'].split(',')
                        for i, param in enumerate(params):
                            param = param.strip()
                            if param:
                                param_parts = param.split(' ')
                                if len(param_parts) >= 2:
                                    param_name = param_parts[0]
                                    param_type = ' '.join(param_parts[1:])
                                    param_list.append({
                                        'name': param_name,
                                        'type': param_type,
                                        'position': i + 1
                                    })
                    
                    # Create procedure object
                    procedure = StoredProcedure(
                        name=row_dict['procedure_name'],
                        schema=row_dict['schema_name'],
                        type=row_dict['routine_type'],
                        parameters=param_list,
                        return_type=row_dict['return_type'] if row_dict['routine_type'] == 'FUNCTION' else None,
                        body=row_dict['source'] or row_dict['procedure_body'] or ''
                    )
                    
                    # Add to dictionary
                    procedures[f"{procedure.schema}.{procedure.name}"] = procedure
                    
            return procedures
                
        except Exception as e:
            self.logger.error(f"Error extracting PostgreSQL procedures: {str(e)}")
            return {}
    
    async def _extract_mysql_procedures(self, engine: Engine, 
                                      schema_filter: Optional[List[str]] = None) -> Dict[str, StoredProcedure]:
        """
        Extract stored procedures and functions from MySQL.
        
        Args:
            engine: SQLAlchemy engine
            schema_filter: Optional list of schemas to include
            
        Returns:
            Dictionary of extracted procedures
        """
        procedures = {}
        loop = asyncio.get_event_loop()
        
        try:
            # Build schema filter condition
            schema_condition = ""
            if schema_filter:
                schema_list = "', '".join(schema_filter)
                schema_condition = f"AND routine_schema IN ('{schema_list}')"
            else:
                schema_condition = f"AND routine_schema = '{engine.url.database}'"
                
            # Query to get procedures and functions
            query = text(f"""
                SELECT 
                    routine_schema,
                    routine_name,
                    routine_type,
                    data_type AS return_type,
                    routine_definition,
                    created,
                    last_altered
                FROM 
                    information_schema.routines
                WHERE 
                    routine_type IN ('PROCEDURE', 'FUNCTION')
                    {schema_condition}
                ORDER BY 
                    routine_schema, routine_name;
            """)
            
            # Execute query
            with engine.connect() as conn:
                result = await loop.run_in_executor(None, lambda: conn.execute(query))
                rows = await loop.run_in_executor(None, lambda: result.fetchall())
                
                # Process results
                for row in rows:
                    row_dict = dict(row._mapping)
                    
                    # Get parameters for this routine
                    param_query = text("""
                        SELECT 
                            parameter_name,
                            data_type,
                            ordinal_position,
                            parameter_mode
                        FROM 
                            information_schema.parameters
                        WHERE 
                            specific_schema = :schema
                            AND specific_name = :name
                        ORDER BY 
                            ordinal_position;
                    """)
                    
                    param_result = await loop.run_in_executor(
                        None, 
                        lambda: conn.execute(
                            param_query, 
                            {"schema": row_dict['routine_schema'], "name": row_dict['routine_name']}
                        )
                    )
                    param_rows = await loop.run_in_executor(None, lambda: param_result.fetchall())
                    
                    # Parse parameters
                    param_list = []
                    for param_row in param_rows:
                        param_dict = dict(param_row._mapping)
                        # Skip return parameter for functions
                        if param_dict['parameter_name'] is None:
                            continue
                        param_list.append({
                            'name': param_dict['parameter_name'],
                            'type': param_dict['data_type'],
                            'position': param_dict['ordinal_position'],
                            'mode': param_dict['parameter_mode']
                        })
                    
                    # Create procedure object
                    procedure = StoredProcedure(
                        name=row_dict['routine_name'],
                        schema=row_dict['routine_schema'],
                        type=row_dict['routine_type'],
                        parameters=param_list,
                        return_type=row_dict['return_type'] if row_dict['routine_type'] == 'FUNCTION' else None,
                        body=row_dict['routine_definition'] or '',
                        created_at=str(row_dict['created']) if row_dict['created'] else None,
                        last_modified=str(row_dict['last_altered']) if row_dict['last_altered'] else None
                    )
                    
                    # Add to dictionary
                    procedures[f"{procedure.schema}.{procedure.name}"] = procedure
                    
            return procedures
                
        except Exception as e:
            self.logger.error(f"Error extracting MySQL procedures: {str(e)}")
            return {}
    
    async def _extract_sqlserver_procedures(self, engine: Engine, 
                                         schema_filter: Optional[List[str]] = None) -> Dict[str, StoredProcedure]:
        """
        Extract stored procedures and functions from SQL Server.
        
        Args:
            engine: SQLAlchemy engine
            schema_filter: Optional list of schemas to include
            
        Returns:
            Dictionary of extracted procedures
        """
        procedures = {}
        loop = asyncio.get_event_loop()
        
        try:
            # Build schema filter condition
            schema_condition = ""
            if schema_filter:
                schema_list = "', '".join(schema_filter)
                schema_condition = f"AND s.name IN ('{schema_list}')"
            else:
                schema_condition = "AND s.name NOT IN ('sys', 'INFORMATION_SCHEMA')"
                
            # Query to get procedures
            proc_query = text(f"""
                SELECT 
                    s.name AS schema_name,
                    p.name AS procedure_name,
                    'PROCEDURE' AS routine_type,
                    OBJECT_DEFINITION(p.object_id) AS procedure_body,
                    p.create_date,
                    p.modify_date
                FROM 
                    sys.procedures p
                    JOIN sys.schemas s ON p.schema_id = s.schema_id
                WHERE 
                    p.is_ms_shipped = 0
                    {schema_condition}
                ORDER BY 
                    s.name, p.name;
            """)
            
            # Query to get functions
            func_query = text(f"""
                SELECT 
                    s.name AS schema_name,
                    f.name AS procedure_name,
                    CASE 
                        WHEN f.type_desc = 'SQL_SCALAR_FUNCTION' THEN 'SCALAR_FUNCTION'
                        WHEN f.type_desc = 'SQL_TABLE_VALUED_FUNCTION' THEN 'TABLE_FUNCTION'
                        ELSE 'FUNCTION'
                    END AS routine_type,
                    OBJECT_DEFINITION(f.object_id) AS procedure_body,
                    f.create_date,
                    f.modify_date
                FROM 
                    sys.objects f
                    JOIN sys.schemas s ON f.schema_id = s.schema_id
                WHERE 
                    f.type IN ('FN', 'IF', 'TF')
                    AND f.is_ms_shipped = 0
                    {schema_condition}
                ORDER BY 
                    s.name, f.name;
            """)
            
            # Execute procedure query
            with engine.connect() as conn:
                # Get procedures
                proc_result = await loop.run_in_executor(None, lambda: conn.execute(proc_query))
                proc_rows = await loop.run_in_executor(None, lambda: proc_result.fetchall())
                
                # Process procedure results
                for row in proc_rows:
                    row_dict = dict(row._mapping)
                    
                    # Get parameters for this procedure
                    param_query = text("""
                        SELECT 
                            p.name AS parameter_name,
                            t.name AS data_type,
                            p.parameter_id AS ordinal_position,
                            p.is_output AS is_output
                        FROM 
                            sys.parameters p
                            JOIN sys.types t ON p.system_type_id = t.system_type_id
                        WHERE 
                            p.object_id = OBJECT_ID(:proc_name)
                        ORDER BY 
                            p.parameter_id;
                    """)
                    
                    full_proc_name = f"{row_dict['schema_name']}.{row_dict['procedure_name']}"
                    param_result = await loop.run_in_executor(
                        None, 
                        lambda: conn.execute(param_query, {"proc_name": full_proc_name})
                    )
                    param_rows = await loop.run_in_executor(None, lambda: param_result.fetchall())
                    
                    # Parse parameters
                    param_list = []
                    for param_row in param_rows:
                        param_dict = dict(param_row._mapping)
                        param_list.append({
                            'name': param_dict['parameter_name'],
                            'type': param_dict['data_type'],
                            'position': param_dict['ordinal_position'],
                            'is_output': bool(param_dict['is_output'])
                        })
                    
                    # Create procedure object
                    procedure = StoredProcedure(
                        name=row_dict['procedure_name'],
                        schema=row_dict['schema_name'],
                        type=row_dict['routine_type'],
                        parameters=param_list,
                        body=row_dict['procedure_body'] or '',
                        created_at=str(row_dict['create_date']) if row_dict['create_date'] else None,
                        last_modified=str(row_dict['modify_date']) if row_dict['modify_date'] else None
                    )
                    
                    # Add to dictionary
                    procedures[f"{procedure.schema}.{procedure.name}"] = procedure
                
                # Get functions
                func_result = await loop.run_in_executor(None, lambda: conn.execute(func_query))
                func_rows = await loop.run_in_executor(None, lambda: func_result.fetchall())
                
                # Process function results
                for row in func_rows:
                    row_dict = dict(row._mapping)
                    
                    # Get parameters for this function
                    param_query = text("""
                        SELECT 
                            p.name AS parameter_name,
                            t.name AS data_type,
                            p.parameter_id AS ordinal_position,
                            p.is_output AS is_output
                        FROM 
                            sys.parameters p
                            JOIN sys.types t ON p.system_type_id = t.system_type_id
                        WHERE 
                            p.object_id = OBJECT_ID(:func_name)
                        ORDER BY 
                            p.parameter_id;
                    """)
                    
                    full_func_name = f"{row_dict['schema_name']}.{row_dict['procedure_name']}"
                    param_result = await loop.run_in_executor(
                        None, 
                        lambda: conn.execute(param_query, {"func_name": full_func_name})
                    )
                    param_rows = await loop.run_in_executor(None, lambda: param_result.fetchall())
                    
                    # Parse parameters
                    param_list = []
                    for param_row in param_rows:
                        param_dict = dict(param_row._mapping)
                        param_list.append({
                            'name': param_dict['parameter_name'],
                            'type': param_dict['data_type'],
                            'position': param_dict['ordinal_position'],
                            'is_output': bool(param_dict['is_output'])
                        })
                    
                    # Get return type for function
                    return_type = None
                    if 'FUNCTION' in row_dict['routine_type']:
                        return_type_query = text("""
                            SELECT 
                                t.name AS return_type
                            FROM 
                                sys.objects o
                                JOIN sys.types t ON o.system_type_id = t.system_type_id
                            WHERE 
                                o.object_id = OBJECT_ID(:func_name);
                        """)
                        
                        try:
                            return_result = await loop.run_in_executor(
                                None, 
                                lambda: conn.execute(return_type_query, {"func_name": full_func_name})
                            )
                            return_row = await loop.run_in_executor(None, lambda: return_result.fetchone())
                            if return_row:
                                return_type = return_row.return_type
                        except Exception as e:
                            self.logger.warning(f"Could not get return type for function {full_func_name}: {str(e)}")
                    
                    # Create procedure object
                    procedure = StoredProcedure(
                        name=row_dict['procedure_name'],
                        schema=row_dict['schema_name'],
                        type=row_dict['routine_type'],
                        parameters=param_list,
                        return_type=return_type,
                        body=row_dict['procedure_body'] or '',
                        created_at=str(row_dict['create_date']) if row_dict['create_date'] else None,
                        last_modified=str(row_dict['modify_date']) if row_dict['modify_date'] else None
                    )
                    
                    # Add to dictionary
                    procedures[f"{procedure.schema}.{procedure.name}"] = procedure
                    
            return procedures
                
        except Exception as e:
            self.logger.error(f"Error extracting SQL Server procedures: {str(e)}")
            return {}
    
    async def _extract_sybase_procedures(self, engine: Engine, 
                                      schema_filter: Optional[List[str]] = None) -> Dict[str, StoredProcedure]:
        """
        Extract stored procedures and functions from Sybase.
        
        Args:
            engine: SQLAlchemy engine
            schema_filter: Optional list of schemas to include
            
        Returns:
            Dictionary of extracted procedures
        """
        # Sybase extraction is similar to SQL Server
        return await self._extract_sqlserver_procedures(engine, schema_filter)
