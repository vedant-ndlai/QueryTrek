"""
LangGraph-based Orchestrator for coordinating the multi-agent system.
This is a proof-of-concept implementation showing how LangGraph could improve
the VMigrateAgent architecture.
"""
import logging
import time
import os
import json
from typing import Dict, Any, List, Optional, Set, Tuple, TypedDict, Annotated, Literal
import asyncio
from datetime import datetime
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.graph.message import AnyMessage
from langgraph.checkpoint import JsonCheckpoint
from langgraph.viz import visualize

from ..models.schema import DatabaseSchema, DatabaseType
from .base_agent import BaseAgent
from .connection_agent import ConnectionAgent
from .table_agent import TableAgent
from .relationship_agent import RelationshipAgent
from .procedure_agent import ProcedureAgent
from .dependency_agent import DependencyAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("LangGraphOrchestrator")

# Define the state schema for our agent workflow
class AgentState(TypedDict):
    """State schema for the agent workflow."""
    # Input parameters
    connection_string: str
    schema_filter: Optional[List[str]]
    
    # Connection information
    engine: Optional[Any]
    database_type: Optional[str]
    database_name: Optional[str]
    
    # Extraction results
    tables: Optional[Dict[str, Any]]
    procedures: Optional[Dict[str, Any]]
    relationships: Optional[Dict[str, Any]]
    
    # Final schema
    schema: Optional[Any]
    
    # Status tracking
    status: str
    error: Optional[str]
    execution_time: Optional[float]

# Agent node implementations
async def connection_agent_node(state: AgentState) -> AgentState:
    """Connection agent node that establishes database connection and detects type."""
    logger.info("Connection agent starting")
    start_time = time.time()
    node_name = "connection"
    
    try:
        # Initialize the agent
        agent = ConnectionAgent()
        
        # Execute the agent
        result = await agent.execute({
            "connection_string": state["connection_string"]
        })
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Track node execution time
        node_execution_times = state.get("node_execution_times", {})
        node_execution_times[node_name] = execution_time
        
        # Update state with connection results
        return {
            **state,
            "engine": result["engine"],
            "database_type": result["database_type"],
            "database_name": result["database_name"],
            "status": "connection_complete",
            "execution_time": execution_time,
            "node_execution_times": node_execution_times
        }
    except Exception as e:
        logger.error(f"Connection agent error: {str(e)}")
        # Track execution time even for errors
        execution_time = time.time() - start_time
        node_execution_times = state.get("node_execution_times", {})
        node_execution_times[node_name] = execution_time
        
        return {
            **state,
            "status": "error",
            "error": f"Connection error: {str(e)}",
            "execution_time": execution_time,
            "node_execution_times": node_execution_times
        }

async def table_agent_node(state: AgentState) -> AgentState:
    """Table agent node that extracts tables and their metadata."""
    logger.info("Table agent starting")
    start_time = time.time()
    
    try:
        # Initialize the agent
        agent = TableAgent()
        
        # Execute the agent
        result = await agent.execute({
            "engine": state["engine"],
            "database_type": state["database_type"],
            "database_name": state["database_name"],
            "schema_filter": state.get("schema_filter")
        })
        
        # Update state with table results
        return {
            **state,
            "tables": result["tables"],
            "status": "tables_extracted",
            "execution_time": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Table agent error: {str(e)}")
        return {
            **state,
            "status": "error",
            "error": f"Table extraction error: {str(e)}",
            "execution_time": time.time() - start_time
        }

async def procedure_agent_node(state: AgentState) -> AgentState:
    """Procedure agent node that extracts stored procedures and functions."""
    logger.info("Procedure agent starting")
    start_time = time.time()
    
    try:
        # Initialize the agent
        agent = ProcedureAgent()
        
        # Execute the agent
        result = await agent.execute({
            "engine": state["engine"],
            "database_type": state["database_type"],
            "database_name": state["database_name"],
            "schema_filter": state.get("schema_filter")
        })
        
        # Update state with procedure results
        return {
            **state,
            "procedures": result["procedures"],
            "status": "procedures_extracted",
            "execution_time": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Procedure agent error: {str(e)}")
        return {
            **state,
            "status": "error",
            "error": f"Procedure extraction error: {str(e)}",
            "execution_time": time.time() - start_time
        }

async def parallel_extraction_node(state: AgentState) -> AgentState:
    """Node that runs table and procedure extraction in parallel."""
    logger.info("Starting parallel extraction of tables and procedures")
    start_time = time.time()
    
    try:
        # Create tasks for parallel execution
        table_task = asyncio.create_task(table_agent_node(state))
        procedure_task = asyncio.create_task(procedure_agent_node(state))
        
        # Wait for both tasks to complete
        table_state, procedure_state = await asyncio.gather(table_task, procedure_task)
        
        # Merge results from both agents
        return {
            **state,
            "tables": table_state["tables"],
            "procedures": procedure_state["procedures"],
            "status": "parallel_extraction_complete",
            "execution_time": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Parallel extraction error: {str(e)}")
        return {
            **state,
            "status": "error",
            "error": f"Parallel extraction error: {str(e)}",
            "execution_time": time.time() - start_time
        }

async def relationship_agent_node(state: AgentState) -> AgentState:
    """Relationship agent node that extracts foreign key relationships."""
    logger.info("Relationship agent starting")
    start_time = time.time()
    
    try:
        # Initialize the agent
        agent = RelationshipAgent()
        
        # Execute the agent
        result = await agent.execute({
            "engine": state["engine"],
            "database_type": state["database_type"],
            "tables": state["tables"]
        })
        
        # Update state with relationship results
        return {
            **state,
            "relationships": result["tables"],  # This contains updated tables with relationships
            "status": "relationships_extracted",
            "execution_time": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Relationship agent error: {str(e)}")
        return {
            **state,
            "status": "error",
            "error": f"Relationship extraction error: {str(e)}",
            "execution_time": time.time() - start_time
        }

async def dependency_agent_node(state: AgentState) -> AgentState:
    """Dependency agent node that analyzes dependencies between database objects."""
    logger.info("Dependency agent starting")
    start_time = time.time()
    
    try:
        # Initialize the agent
        agent = DependencyAgent()
        
        # Create schema object with tables and procedures
        schema = DatabaseSchema(
            database_name=state["database_name"],
            database_type=state["database_type"]
        )
        
        # Add tables with relationships
        for table_key, table in state["relationships"].items():
            schema.add_table(table)
            
        # Add procedures
        for proc_key, proc in state["procedures"].items():
            schema.add_procedure(proc)
        
        # Execute the agent
        result = await agent.execute({
            "engine": state["engine"],
            "database_type": state["database_type"],
            "database_name": state["database_name"],
            "schema": schema
        })
        
        # Update state with final schema including dependencies
        return {
            **state,
            "schema": result["schema"],
            "status": "dependencies_analyzed",
            "execution_time": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Dependency agent error: {str(e)}")
        return {
            **state,
            "status": "error",
            "error": f"Dependency analysis error: {str(e)}",
            "execution_time": time.time() - start_time
        }

async def finalize_node(state: AgentState) -> AgentState:
    """Finalize the extraction process and prepare the result."""
    logger.info("Finalizing extraction process")
    
    return {
        **state,
        "status": "complete"
    }

async def error_handler_node(state: AgentState) -> AgentState:
    """Handle errors in the extraction process."""
    logger.error(f"Error in extraction process: {state.get('error', 'Unknown error')}")
    
    return {
        **state,
        "status": "error_handled"
    }

class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator for the VMigrateAgent system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LangGraph orchestrator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger("LangGraphOrchestrator")
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for schema extraction.
        
        Returns:
            Compiled StateGraph
        """
        # Create checkpoint directory if it doesn't exist
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.checkpoint_dir = os.path.join(os.getcwd(), "checkpoints")
        self.checkpoint_path = os.path.join(self.checkpoint_dir, f"langgraph_orchestrator_{timestamp}")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        # Create a checkpoint for visualization and tracing
        # Using a timestamped checkpoint allows multiple runs to be preserved
        checkpoint = JsonCheckpoint(self.checkpoint_path)
        
        # Create the graph with our state schema and checkpoint
        workflow = StateGraph(AgentState, checkpoint=checkpoint)
        
        # Add nodes for each agent
        workflow.add_node("connection", connection_agent_node)
        workflow.add_node("parallel_extraction", parallel_extraction_node)
        workflow.add_node("relationship", relationship_agent_node)
        workflow.add_node("dependency", dependency_agent_node)
        workflow.add_node("finalize", finalize_node)
        workflow.add_node("error_handler", error_handler_node)
        
        # Define conditional routing based on status
        def route_after_connection(state: AgentState) -> str:
            if state["status"] == "error":
                return "error_handler"
            return "parallel_extraction"
        
        def route_after_parallel_extraction(state: AgentState) -> str:
            if state["status"] == "error":
                return "error_handler"
            return "relationship"
        
        def route_after_relationship(state: AgentState) -> str:
            if state["status"] == "error":
                return "error_handler"
            return "dependency"
        
        def route_after_dependency(state: AgentState) -> str:
            if state["status"] == "error":
                return "error_handler"
            return "finalize"
        
        def route_after_error_handler(state: AgentState) -> str:
            return "end"
        
        def route_after_finalize(state: AgentState) -> str:
            return "end"
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "connection",
            route_after_connection
        )
        
        workflow.add_conditional_edges(
            "parallel_extraction",
            route_after_parallel_extraction
        )
        
        workflow.add_conditional_edges(
            "relationship",
            route_after_relationship
        )
        
        workflow.add_conditional_edges(
            "dependency",
            route_after_dependency
        )
        
        workflow.add_conditional_edges(
            "error_handler",
            route_after_error_handler
        )
        
        workflow.add_conditional_edges(
            "finalize",
            route_after_finalize
        )
        
        # Set the entry point
        workflow.set_entry_point("connection")
        
        # Add end node
        workflow.add_node("end", lambda x: x)
        
        # Compile the graph
        return workflow.compile()
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the schema extraction process using LangGraph.
        
        Args:
            data: Dictionary containing:
                - connection_string: Database connection string
                - schema_filter: Optional list of schemas to include
                
        Returns:
            Dictionary with extracted schema and metadata
        """
        connection_string = data.get("connection_string")
        if not connection_string:
            raise ValueError("Connection string is required")
            
        schema_filter = data.get("schema_filter")
        
        # Create a sanitized connection string for logging (remove credentials)
        if "@" in connection_string:
            sanitized_connection = connection_string.split("@")[-1]
        else:
            sanitized_connection = connection_string
            
        self.logger.info(f"Starting schema extraction for {sanitized_connection}")
        start_time = time.time()
        
        # Initialize the state
        initial_state = {
            "connection_string": connection_string,
            "schema_filter": schema_filter,
            "engine": None,
            "database_type": None,
            "database_name": None,
            "tables": None,
            "procedures": None,
            "relationships": None,
            "schema": None,
            "status": "initialized",
            "error": None,
            "execution_time": None,
            "start_time": start_time,
            "node_execution_times": {}
        }
        
        # Execute the graph
        config = {"recursion_limit": 25}  # Prevent infinite loops
        result = await self.graph.ainvoke(initial_state, config=config)
        
        end_time = time.time()
        total_execution_time = end_time - start_time
        self.logger.info(f"Schema extraction completed in {total_execution_time:.2f} seconds")
        
        # Check if extraction was successful
        if result["status"] == "complete":
            # Generate visualization HTML file
            viz_file = None
            trace_file = None
            metrics_file = None
            
            try:
                # Create visualization directory if it doesn't exist
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                viz_path = os.path.join(os.getcwd(), "visualizations")
                os.makedirs(viz_path, exist_ok=True)
                
                # Generate a unique filename based on timestamp and database name
                db_name = result["database_name"] or "unknown_db"
                db_name = db_name.replace(" ", "_").lower()
                base_filename = f"{db_name}_{timestamp}"
                
                # 1. Generate the HTML visualization
                viz_file = os.path.join(viz_path, f"{base_filename}_workflow.html")
                
                # Get the trace from the checkpoint
                trace = self.graph.get_trace()
                if trace:
                    # Create visualization
                    viz = visualize(self.graph, trace)
                    with open(viz_file, "w") as f:
                        f.write(viz.html)
                    self.logger.info(f"Workflow visualization saved to {viz_file}")
                    
                    # 2. Save the trace data for further analysis
                    trace_file = os.path.join(viz_path, f"{base_filename}_trace.json")
                    with open(trace_file, "w") as f:
                        # Convert trace to a serializable format
                        serializable_trace = []
                        for event in trace:
                            # Convert any non-serializable objects to strings
                            serializable_event = {}
                            for k, v in event.items():
                                try:
                                    json.dumps({k: v})
                                    serializable_event[k] = v
                                except (TypeError, OverflowError):
                                    serializable_event[k] = str(v)
                            serializable_trace.append(serializable_event)
                        json.dump(serializable_trace, f, indent=2)
                    self.logger.info(f"Workflow trace saved to {trace_file}")
                    
                    # 3. Generate execution metrics
                    metrics_file = os.path.join(viz_path, f"{base_filename}_metrics.json")
                    metrics = {
                        "database": {
                            "name": result["database_name"],
                            "type": str(result["database_type"]),
                            "connection": sanitized_connection
                        },
                        "execution": {
                            "total_time": total_execution_time,
                            "node_times": result.get("node_execution_times", {}),
                            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
                            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
                        },
                        "results": {
                            "tables_count": len(result["schema"].tables) if result["schema"] else 0,
                            "procedures_count": len(result["schema"].procedures) if result["schema"] else 0,
                            "dependencies_count": len(result["schema"].dependencies) if result["schema"] else 0
                        }
                    }
                    with open(metrics_file, "w") as f:
                        json.dump(metrics, f, indent=2)
                    self.logger.info(f"Execution metrics saved to {metrics_file}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to generate visualization or metrics: {str(e)}")
            
            return {
                "schema": result["schema"],
                "database_type": result["database_type"],
                "database_name": result["database_name"],
                "connection_string": connection_string,
                "execution_time": total_execution_time,
                "visualization_path": viz_file,
                "trace_path": trace_file,
                "metrics_path": metrics_file,
                "checkpoint_path": self.checkpoint_path,
                "node_execution_times": result.get("node_execution_times", {})
            }
        else:
            error_message = result.get('error', 'Unknown error')
            self.logger.error(f"Schema extraction failed: {error_message}")
            raise RuntimeError(f"Schema extraction failed: {error_message}")

# Example usage
async def example_usage():
    """Example of how to use the LangGraphOrchestrator."""
    orchestrator = LangGraphOrchestrator()
    
    try:
        result = await orchestrator.process({
            "connection_string": "postgresql://username:password@localhost:5432/dbname"
        })
        
        print(f"Extracted schema for {result['database_name']} ({result['database_type']})")
        print(f"Tables: {len(result['schema'].tables)}")
        print(f"Procedures: {len(result['schema'].procedures)}")
        print(f"Dependencies: {len(result['schema'].dependencies)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())
