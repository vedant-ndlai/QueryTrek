"""
Test script for connecting to the Sybase database and extracting schema.
"""
import asyncio
import os
import sys
import logging
from src.agents.connection_agent import ConnectionAgent
from src.agents.orchestrator_agent import OrchestratorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("SybaseTest")

async def test_connection():
    """Test connection to Sybase database."""
    # Sybase connection string
    connection_string = "DRIVER={FreeTDS};SERVER=localhost;PORT=5000;DATABASE=SampleDB;UID=sa;PWD=sybase123;TDS_VERSION=5.0"
    
    try:
        # Initialize connection agent
        connection_agent = ConnectionAgent()
        
        # Test connection
        result = await connection_agent.process({
            "connection_string": connection_string
        })
        
        logger.info(f"Connection successful: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        return False

async def extract_schema():
    """Extract schema from Sybase database."""
    # Sybase connection string
    connection_string = "DRIVER={FreeTDS};SERVER=localhost;PORT=5000;DATABASE=SampleDB;UID=sa;PWD=sybase123;TDS_VERSION=5.0"
    
    try:
        # Initialize orchestrator agent
        orchestrator = OrchestratorAgent()
        
        # Extract schema
        result = await orchestrator.process({
            "connection_string": connection_string,
            "schema_filter": ["sales", "inventory", "hr"]
        })
        
        schema = result["schema"]
        
        logger.info(f"Schema extracted: {schema.database_name} ({schema.database_type.value})")
        logger.info(f"Tables: {len(schema.tables)}, Procedures: {len(schema.procedures)}, Views: {len(schema.views)}, Dependencies: {len(schema.dependencies)}")
        
        # Print some details
        logger.info("\nTables:")
        for table_key, table in schema.tables.items():
            logger.info(f"  - {table.schema}.{table.name} ({len(table.columns)} columns)")
        
        logger.info("\nProcedures:")
        for proc_key, proc in schema.procedures.items():
            logger.info(f"  - {proc.schema}.{proc.name} ({proc.type})")
        
        logger.info("\nViews:")
        for view_key, view in schema.views.items():
            logger.info(f"  - {view.schema}.{view.name}")
        
        logger.info("\nDependencies:")
        for dep in schema.dependencies[:10]:  # Show first 10 dependencies
            logger.info(f"  - {dep.source_schema}.{dep.source_name} -> {dep.target_schema}.{dep.target_name} ({dep.dependency_type})")
        
        return schema
        
    except Exception as e:
        logger.error(f"Schema extraction failed: {str(e)}")
        return None

async def main():
    """Main function."""
    logger.info("Testing Sybase connection and schema extraction")
    
    # Test connection
    connection_successful = await test_connection()
    
    if connection_successful:
        # Extract schema
        schema = await extract_schema()
        
        if schema:
            logger.info("Schema extraction successful")
        else:
            logger.error("Schema extraction failed")
    else:
        logger.error("Connection test failed")

if __name__ == "__main__":
    asyncio.run(main())
