"""
Orchestrator Agent for coordinating the multi-agent system.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
import time

from ..models.schema import DatabaseSchema, DatabaseType
from .base_agent import BaseAgent
from .connection_agent import ConnectionAgent
from .table_agent import TableAgent
from .relationship_agent import RelationshipAgent
from .procedure_agent import ProcedureAgent
from .dependency_agent import DependencyAgent

class OrchestratorAgent(BaseAgent):
    """
    Master agent responsible for orchestrating the multi-agent system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("Orchestrator", config)
        
        # Initialize sub-agents
        self.connection_agent = ConnectionAgent(config)
        self.table_agent = TableAgent(config)
        self.relationship_agent = RelationshipAgent(config)
        self.procedure_agent = ProcedureAgent(config)
        self.dependency_agent = DependencyAgent(config)
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the schema extraction process.
        
        Args:
            data: Dictionary containing:
                - connection_string: Database connection string
                - schema_filter: Optional list of schemas to include
                
        Returns:
            Dictionary with extracted schema
        """
        connection_string = data.get("connection_string")
        if not connection_string:
            raise ValueError("Connection string is required")
            
        schema_filter = data.get("schema_filter")
        
        self.logger.info(f"Starting schema extraction for {connection_string}")
        start_time = time.time()
        
        # Step 1: Connect to database and detect type
        self.logger.info("Step 1: Establishing database connection")
        connection_data = await self.connection_agent.execute({
            "connection_string": connection_string
        })
        
        engine = connection_data["engine"]
        database_type = connection_data["database_type"]
        database_name = connection_data["database_name"]
        
        # Create schema object
        schema = DatabaseSchema(
            database_name=database_name,
            database_type=database_type
        )
        
        # Step 2: Extract tables (run in parallel with procedures)
        self.logger.info("Step 2: Extracting tables and procedures")
        
        # Create tasks for parallel execution
        table_task = asyncio.create_task(self.table_agent.execute({
            "engine": engine,
            "database_type": database_type,
            "database_name": database_name,
            "schema_filter": schema_filter
        }))
        
        procedure_task = asyncio.create_task(self.procedure_agent.execute({
            "engine": engine,
            "database_type": database_type,
            "database_name": database_name,
            "schema_filter": schema_filter
        }))
        
        # Wait for both tasks to complete
        table_data, procedure_data = await asyncio.gather(table_task, procedure_task)
        
        # Update schema with tables and procedures
        for table_key, table in table_data["tables"].items():
            schema.add_table(table)
            
        for proc_key, proc in procedure_data["procedures"].items():
            schema.add_procedure(proc)
        
        # Step 3: Extract relationships
        self.logger.info("Step 3: Extracting relationships")
        relationship_data = await self.relationship_agent.execute({
            "engine": engine,
            "database_type": database_type,
            "tables": schema.tables
        })
        
        # Update schema with relationships
        for table_key, table in relationship_data["tables"].items():
            schema.tables[table_key] = table
        
        # Step 4: Analyze dependencies
        self.logger.info("Step 4: Analyzing dependencies")
        dependency_data = await self.dependency_agent.execute({
            "engine": engine,
            "database_type": database_type,
            "database_name": database_name,
            "schema": schema
        })
        
        # Get updated schema with dependencies
        schema = dependency_data["schema"]
        
        end_time = time.time()
        self.logger.info(f"Schema extraction completed in {end_time - start_time:.2f} seconds")
        
        return {
            "schema": schema,
            "database_type": database_type,
            "database_name": database_name,
            "connection_string": connection_string
        }
