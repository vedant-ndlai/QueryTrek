"""
Main application for VMigrateAgent - Multi-Agent Database Schema Extraction System.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

from .agents.orchestrator_agent import OrchestratorAgent
from .agents.graph_agent import GraphAgent
from .agents.llm_agent import LLMAgent
from .utils.visualizer import SchemaVisualizer
from .utils.message_broker import MessageBroker, TaskQueue
from .api.api import app

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("vmigrateagent.log")
    ]
)

logger = logging.getLogger("VMigrateAgent")

async def extract_schema(connection_string: str, schema_filter: Optional[List[str]] = None, 
                        output_dir: str = "output", visualize: bool = True) -> None:
    """
    Extract schema from a database.
    
    Args:
        connection_string: Database connection string
        schema_filter: Optional list of schemas to extract
        output_dir: Output directory for visualization files
        visualize: Whether to generate visualization
    """
    try:
        logger.info("Starting schema extraction")
        
        # Initialize orchestrator agent
        orchestrator = OrchestratorAgent()
        
        # Extract schema
        result = await orchestrator.process({
            "connection_string": connection_string,
            "schema_filter": schema_filter
        })
        
        schema = result["schema"]
        
        logger.info(f"Schema extracted: {schema.database_name} ({schema.database_type.value})")
        logger.info(f"Tables: {len(schema.tables)}, Procedures: {len(schema.procedures)}, Views: {len(schema.views)}, Dependencies: {len(schema.dependencies)}")
        
        # Store in Neo4j
        try:
            logger.info("Storing schema in Neo4j")
            graph_agent = GraphAgent()
            await graph_agent.process({
                "schema": schema,
                "database_name": schema.database_name,
                "database_type": schema.database_type
            })
            logger.info("Schema stored in Neo4j")
        except Exception as e:
            logger.error(f"Error storing schema in Neo4j: {str(e)}")
        
        # Generate visualization
        if visualize:
            try:
                logger.info("Generating visualization")
                visualizer = SchemaVisualizer()
                
                # Create output directory
                os.makedirs(output_dir, exist_ok=True)
                
                # Generate dependency graph
                html_path = visualizer.generate_dependency_graph(schema, output_dir)
                logger.info(f"Dependency graph generated: {html_path}")
                
                # Generate JSON representation
                json_path = os.path.join(output_dir, f"{schema.database_name}_schema.json")
                visualizer.generate_json_representation(schema, json_path)
                logger.info(f"JSON representation generated: {json_path}")
            except Exception as e:
                logger.error(f"Error generating visualization: {str(e)}")
        
        logger.info("Schema extraction completed")
        
    except Exception as e:
        logger.error(f"Error extracting schema: {str(e)}")
        raise

async def analyze_schema(database_name: str, analysis_type: str = "dependency", 
                        target_object: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Analyze schema using LLM.
    
    Args:
        database_name: Name of the database
        analysis_type: Type of analysis to perform
        target_object: Optional target object for impact analysis
        
    Returns:
        Analysis results
    """
    try:
        logger.info(f"Starting schema analysis: {analysis_type}")
        
        # Initialize graph agent to retrieve schema
        graph_agent = GraphAgent()
        
        # Retrieve schema from Neo4j
        schema_result = await graph_agent.process({
            "action": "get_schema",
            "database_name": database_name
        })
        
        schema = schema_result["schema"]
        
        # Initialize LLM agent
        llm_agent = LLMAgent()
        
        # Perform analysis
        analysis_result = await llm_agent.process({
            "schema": schema,
            "analysis_type": analysis_type,
            "target_object": target_object
        })
        
        logger.info(f"Schema analysis completed: {analysis_type}")
        
        return analysis_result["result"]
        
    except Exception as e:
        logger.error(f"Error analyzing schema: {str(e)}")
        raise

def start_api_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Start the API server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

async def main() -> None:
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description="VMigrateAgent - Multi-Agent Database Schema Extraction System")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Extract schema command
    extract_parser = subparsers.add_parser("extract", help="Extract schema from a database")
    extract_parser.add_argument("--connection", "-c", required=True, help="Database connection string")
    extract_parser.add_argument("--schemas", "-s", nargs="+", help="Schemas to extract")
    extract_parser.add_argument("--output", "-o", default="output", help="Output directory")
    extract_parser.add_argument("--no-visualize", action="store_true", help="Disable visualization generation")
    
    # Analyze schema command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze schema using LLM")
    analyze_parser.add_argument("--database", "-d", required=True, help="Database name")
    analyze_parser.add_argument("--type", "-t", default="dependency", choices=["dependency", "optimization", "impact"], help="Analysis type")
    analyze_parser.add_argument("--target", help="Target object for impact analysis (JSON format)")
    analyze_parser.add_argument("--output", "-o", help="Output file for analysis results")
    
    # Start API server command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to bind to")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "extract":
        await extract_schema(
            connection_string=args.connection,
            schema_filter=args.schemas,
            output_dir=args.output,
            visualize=not args.no_visualize
        )
    elif args.command == "analyze":
        target_object = None
        if args.target:
            try:
                target_object = json.loads(args.target)
            except json.JSONDecodeError:
                logger.error("Invalid JSON format for target object")
                sys.exit(1)
        
        result = await analyze_schema(
            database_name=args.database,
            analysis_type=args.type,
            target_object=target_object
        )
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
    elif args.command == "api":
        start_api_server(host=args.host, port=args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
