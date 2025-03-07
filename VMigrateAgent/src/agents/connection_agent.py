"""
Connection Agent for handling database connections and type detection.
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple
import asyncio
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from urllib.parse import urlparse

from ..models.schema import DatabaseType
from .base_agent import BaseAgent

class ConnectionAgent(BaseAgent):
    """
    Agent responsible for establishing database connections and detecting database types.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the connection agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("Connection", config)
        self.engines = {}
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process connection request and detect database type.
        
        Args:
            data: Dictionary containing connection information
                - connection_string: Database connection string
                
        Returns:
            Dictionary with connection details and database type
        """
        connection_string = data.get("connection_string")
        if not connection_string:
            raise ValueError("Connection string is required")
            
        self.logger.info(f"Processing connection request for: {self._mask_password(connection_string)}")
        
        # Detect database type from connection string
        db_type = self._detect_db_type(connection_string)
        
        # Create engine and test connection
        engine = await self._create_engine(connection_string, db_type)
        
        # Get database name
        db_name = self._get_database_name(connection_string)
        
        return {
            "connection_string": connection_string,
            "database_type": db_type,
            "database_name": db_name,
            "engine": engine
        }
    
    def _detect_db_type(self, connection_string: str) -> DatabaseType:
        """
        Detect database type from connection string.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Detected database type
        """
        lower_conn = connection_string.lower()
        
        if "postgresql" in lower_conn or "postgres" in lower_conn:
            return DatabaseType.POSTGRESQL
        elif "mysql" in lower_conn:
            return DatabaseType.MYSQL
        elif "mssql" in lower_conn or "sqlserver" in lower_conn:
            return DatabaseType.SQLSERVER
        elif "sybase" in lower_conn:
            return DatabaseType.SYBASE
        else:
            # Try to detect from driver name
            match = re.search(r"^([a-zA-Z]+)(\+[a-zA-Z]+)?://", lower_conn)
            if match:
                driver = match.group(1)
                if driver in ["postgresql", "postgres"]:
                    return DatabaseType.POSTGRESQL
                elif driver == "mysql":
                    return DatabaseType.MYSQL
                elif driver in ["mssql", "sqlserver"]:
                    return DatabaseType.SQLSERVER
                elif driver == "sybase":
                    return DatabaseType.SYBASE
                    
        return DatabaseType.UNKNOWN
    
    async def _create_engine(self, connection_string: str, db_type: DatabaseType) -> sqlalchemy.engine.Engine:
        """
        Create SQLAlchemy engine for the given connection string.
        
        Args:
            connection_string: Database connection string
            db_type: Database type
            
        Returns:
            SQLAlchemy engine
        """
        # Create engine with appropriate parameters based on database type
        connect_args = {}
        
        if db_type == DatabaseType.POSTGRESQL:
            connect_args = {"connect_timeout": 10}
        elif db_type == DatabaseType.MYSQL:
            connect_args = {"connect_timeout": 10}
        elif db_type == DatabaseType.SQLSERVER:
            connect_args = {"timeout": 10}
        
        engine = create_engine(connection_string, connect_args=connect_args)
        
        # Test connection
        try:
            # Use asyncio to run in a separate thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: engine.connect().close())
            self.logger.info(f"Successfully connected to {db_type} database")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise
            
        # Store engine for later use
        self.engines[connection_string] = engine
        return engine
    
    def _get_database_name(self, connection_string: str) -> str:
        """
        Extract database name from connection string.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Database name
        """
        parsed = urlparse(connection_string)
        
        # Extract database name from path
        path = parsed.path
        if path.startswith('/'):
            path = path[1:]
            
        if not path:
            # Try to extract from query parameters
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed.query)
            if 'database' in query_params:
                return query_params['database'][0]
            elif 'dbname' in query_params:
                return query_params['dbname'][0]
                
        return path
    
    def _mask_password(self, connection_string: str) -> str:
        """
        Mask password in connection string for logging purposes.
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Connection string with password masked
        """
        return re.sub(r'(:)([^@]*)(@)', r'\1******\3', connection_string)
    
    async def get_version(self, engine: sqlalchemy.engine.Engine) -> str:
        """
        Get database version.
        
        Args:
            engine: SQLAlchemy engine
            
        Returns:
            Database version string
        """
        try:
            loop = asyncio.get_event_loop()
            with engine.connect() as conn:
                if engine.name == 'postgresql':
                    result = await loop.run_in_executor(None, lambda: conn.execute(text("SELECT version()")).scalar())
                elif engine.name == 'mysql':
                    result = await loop.run_in_executor(None, lambda: conn.execute(text("SELECT version()")).scalar())
                elif engine.name in ['mssql', 'sqlserver']:
                    result = await loop.run_in_executor(None, lambda: conn.execute(text("SELECT @@version")).scalar())
                else:
                    result = "Unknown"
                    
            return str(result)
        except Exception as e:
            self.logger.error(f"Failed to get database version: {str(e)}")
            return "Unknown"
