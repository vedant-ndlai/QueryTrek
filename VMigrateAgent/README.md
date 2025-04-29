# VMigrateAgent: Multi-Agent Database Schema Extraction System

A scalable, multi-agent system that dynamically extracts database schemas from various relational databases (PostgreSQL, MySQL, SQL Server, Sybase) and provides intelligent analysis through specialized agents.

## Table of Contents
- [Features](#features)
- [System Architecture](#system-architecture)
  - [Architecture Overview](#architecture-overview)
  - [Component Diagram](#component-diagram)
  - [Data Flow](#data-flow)
- [Backend Components](#backend-components)
  - [Agent System](#agent-system)
  - [API Layer](#api-layer)
  - [Database Connectors](#database-connectors)
- [Frontend Components](#frontend-components)
- [Deployment Architecture](#deployment-architecture)
- [LangGraph Integration](#langgraph-integration)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [License](#license)

## Features

- Dynamic database type detection and connection management
- Comprehensive schema metadata extraction
- Advanced dependency analysis between database objects
- Intelligent schema analysis using LLM agents
- Visualization of database schemas and dependencies
- RESTful API for integration with other systems
- Modern React-based frontend for user interaction
- Specialized agents for different aspects of schema extraction:
  - Table extraction
  - Foreign key mapping
  - Stored procedure parsing
  - Dependency resolution

## System Architecture

### Architecture Overview

VMigrateAgent follows a microservices-based architecture with the following key components:

1. **Multi-Agent Backend System**: Core system with specialized agents for different tasks
2. **Neo4j Graph Database**: Stores extracted schema data and relationships
3. **RabbitMQ Message Broker**: Handles asynchronous communication between agents
4. **FastAPI REST API**: Provides external access to the system
5. **React Frontend**: User interface for interacting with the system
6. **Database Connectors**: Adapters for different database systems (PostgreSQL, MySQL, SQL Server, Sybase)

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (React)                           │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           FastAPI REST API                           │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                 ┌─────────────────┴─────────────────┐
                 │                                   │
                 ▼                                   ▼
┌────────────────────────────┐      ┌────────────────────────────────┐
│     Orchestrator Agent     │      │          Graph Agent           │
└────────────┬───────────────┘      └─────────────────┬──────────────┘
             │                                        │
             │                                        │
             ▼                                        ▼
┌────────────────────────────┐      ┌────────────────────────────────┐
│      RabbitMQ Queue        │      │        Neo4j Database          │
└────────────┬───────────────┘      └────────────────────────────────┘
             │
    ┌────────┴─────────┬─────────────┬─────────────┐
    │                  │             │             │
    ▼                  ▼             ▼             ▼
┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ Connection  │  │  Table   │  │Procedure │  │ Dependency   │
│   Agent     │  │  Agent   │  │  Agent   │  │   Agent      │
└─────┬───────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘
      │               │             │               │
      └───────────────┼─────────────┼───────────────┘
                      │             │
                      ▼             ▼
           ┌─────────────────────────────────────┐
           │         Database Connectors         │
           └─────────────────────────────────────┘
                      │             │
                      ▼             ▼
           ┌──────────────┐  ┌─────────────┐
           │  Relational  │  │   Sybase    │
           │  Databases   │  │  Database   │
           └──────────────┘  └─────────────┘
```

### Data Flow

1. **User Interaction**:
   - User submits a database connection request through the frontend
   - Request is sent to the FastAPI backend

2. **Schema Extraction Process**:
   - Orchestrator Agent receives the request and coordinates the extraction process
   - Connection Agent establishes a connection to the target database and detects its type
   - Table Agent and Procedure Agent work in parallel to extract tables and stored procedures
   - Relationship Agent extracts foreign key relationships between tables
   - Dependency Agent analyzes dependencies between database objects

3. **Data Storage and Analysis**:
   - Extracted schema is stored in Neo4j graph database
   - LLM Agent performs intelligent analysis on the schema
   - Results are returned to the frontend for visualization

4. **Visualization and Export**:
   - Frontend displays the schema and dependencies in an interactive visualization
   - User can export the schema to various formats (JSON, HTML)

### Agent Orchestration Flow

The multi-agent system follows a carefully orchestrated workflow managed by the Orchestrator Agent. Here's a detailed flow diagram of how the agents interact:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FastAPI REST API                                             │
└───────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                            │
                                            │ extract-schema request
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Orchestrator Agent                                           │
│                                                                                                 │
│  ┌─────────────────────────────────┐      ┌──────────────────────────────┐                      │
│  │ 1. Receive extraction request   │─────▶│ 2. Initialize extraction     │                      │
│  └─────────────────────────────────┘      └──────────────┬───────────────┘                      │
│                                                          │                                      │
│                                                          ▼                                      │
│  ┌─────────────────────────────────┐      ┌──────────────────────────────┐                      │
│  │ 5. Aggregate results            │◀─────│ 3. Coordinate agent tasks    │                      │
│  └─────────────┬───────────────────┘      └──────────────┬───────────────┘                      │
│                │                                         │                                      │
│                ▼                                         │                                      │
│  ┌─────────────────────────────────┐                     │                                      │
│  │ 6. Return complete schema       │                     │                                      │
│  └─────────────────────────────────┘                     │                                      │
└─────────────────────────────────────────────────────────┬─────────────────────────────────────┘
                                                          │
                                                          │ Parallel execution
                                                          ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Connection Agent│ │   Table Agent   │ │ Procedure Agent │ │Relationship Agent│ │ Dependency Agent│
│                 │ │                 │ │                 │ │                 │ │                 │
│ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │1. Connect to│ │ │ │1. Extract   │ │ │ │1. Extract   │ │ │ │1. Map foreign│ │ │ │1. Analyze   │ │
│ │   database  │ │ │ │   tables    │ │ │ │  procedures │ │ │ │   keys      │ │ │ │dependencies │ │
│ └──────┬──────┘ │ │ └──────┬──────┘ │ │ └──────┬──────┘ │ │ └──────┬──────┘ │ │ └──────┬──────┘ │
│        │        │ │        │        │ │        │        │ │        │        │ │        │        │
│        ▼        │ │        ▼        │ │        ▼        │ │        ▼        │ │        ▼        │
│ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │2. Detect DB │ │ │ │2. Extract   │ │ │ │2. Parse     │ │ │ │2. Identify  │ │ │ │2. Build     │ │
│ │   type      │ │ │ │   columns   │ │ │ │   code      │ │ │ │relationships│ │ │ │   graph     │ │
│ └──────┬──────┘ │ │ └──────┬──────┘ │ │ └──────┬──────┘ │ │ └──────┬──────┘ │ │ └──────┬──────┘ │
│        │        │ │        │        │ │        │        │ │        │        │ │        │        │
│        ▼        │ │        ▼        │ │        ▼        │ │        ▼        │ │        ▼        │
│ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │3. Return    │ │ │ │3. Return    │ │ │ │3. Return    │ │ │ │3. Return    │ │ │ │3. Return    │ │
│ │   metadata  │ │ │ │   tables    │ │ │ │  procedures │ │ │ │relationships│ │ │ │dependencies │ │
│ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
                                                          │
                                                          │ Results
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      Graph Agent                                                │
│                                                                                                 │
│  ┌─────────────────────────────────┐      ┌──────────────────────────────┐                      │
│  │ 1. Receive schema data          │─────▶│ 2. Convert to graph model    │                      │
│  └─────────────────────────────────┘      └──────────────┬───────────────┘                      │
│                                                          │                                      │
│                                                          ▼                                      │
│  ┌─────────────────────────────────┐      ┌──────────────────────────────┐                      │
│  │ 4. Return graph representation  │◀─────│ 3. Store in Neo4j            │                      │
│  └─────────────────────────────────┘      └──────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                          │
                                                          │ Analysis request
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       LLM Agent                                                 │
│                                                                                                 │
│  ┌─────────────────────────────────┐      ┌──────────────────────────────┐                      │
│  │ 1. Receive analysis request     │─────▶│ 2. Formulate LLM prompt      │                      │
│  └─────────────────────────────────┘      └──────────────┬───────────────┘                      │
│                                                          │                                      │
│                                                          ▼                                      │
│  ┌─────────────────────────────────┐      ┌──────────────────────────────┐                      │
│  │ 4. Process and format results   │◀─────│ 3. Send to OpenAI API        │                      │
│  └─────────────┬───────────────────┘      └──────────────────────────────┘                      │
│                │                                                                                │
│                ▼                                                                                │
│  ┌─────────────────────────────────┐                                                            │
│  │ 5. Return analysis results      │                                                            │
│  └─────────────────────────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Orchestration Process Details

1. **Initialization Phase**:
   - The Orchestrator Agent receives an extraction request from the API
   - It initializes the extraction process and prepares to coordinate the specialized agents

2. **Connection Phase**:
   - The Connection Agent is invoked first to establish a database connection
   - It detects the database type (PostgreSQL, MySQL, SQL Server, Sybase)
   - Connection metadata is returned to the Orchestrator Agent

3. **Parallel Extraction Phase**:
   - The Orchestrator Agent creates asynchronous tasks for Table Agent and Procedure Agent
   - These agents work in parallel to extract their respective database objects
   - The Table Agent extracts tables, columns, primary keys, and indexes
   - The Procedure Agent extracts stored procedures, functions, triggers, and views

4. **Relationship Mapping Phase**:
   - Once table extraction is complete, the Relationship Agent maps foreign keys
   - It identifies relationships between tables and updates the schema

5. **Dependency Analysis Phase**:
   - The Dependency Agent analyzes dependencies between all database objects
   - It builds a dependency graph that shows how objects relate to each other

6. **Storage Phase**:
   - The Graph Agent converts the schema to a graph model
   - It stores the schema in the Neo4j graph database for persistence and querying

7. **Analysis Phase (Optional)**:
   - The LLM Agent can be invoked to perform intelligent analysis on the schema
   - It formulates prompts for the OpenAI API based on the analysis type
   - Analysis results are processed and returned to the caller

8. **Result Aggregation**:
   - The Orchestrator Agent aggregates results from all specialized agents
   - It constructs a complete schema representation with all extracted information
   - The final schema is returned to the API for delivery to the frontend

## Backend Components

### Agent System

The multi-agent system consists of the following specialized agents:

1. **Orchestrator Agent**: Coordinates the overall extraction process and manages communication between agents
   - Located in: `src/agents/orchestrator_agent.py`
   - Responsibilities: Task distribution, process coordination, result aggregation

2. **Connection Agent**: Handles database connections and type detection
   - Located in: `src/agents/connection_agent.py`
   - Responsibilities: Establish database connections, detect database type, manage connection pools

3. **Table Agent**: Extracts table definitions and columns
   - Located in: `src/agents/table_agent.py`
   - Responsibilities: Extract tables, columns, primary keys, indexes

4. **Relationship Agent**: Maps foreign keys and table relationships
   - Located in: `src/agents/relationship_agent.py`
   - Responsibilities: Extract foreign keys, identify relationships between tables

5. **Procedure Agent**: Parses stored procedures and functions
   - Located in: `src/agents/procedure_agent.py`
   - Responsibilities: Extract stored procedures, functions, triggers, views

6. **Dependency Agent**: Analyzes dependencies between database objects
   - Located in: `src/agents/dependency_agent.py`
   - Responsibilities: Identify dependencies between database objects, build dependency graph

7. **Graph Agent**: Manages interaction with Neo4j graph database
   - Located in: `src/agents/graph_agent.py`
   - Responsibilities: Store schema in Neo4j, query graph database

8. **LLM Agent**: Performs intelligent analysis using language models
   - Located in: `src/agents/llm_agent.py`
   - Responsibilities: Analyze schema for optimization opportunities, impact analysis

### API Layer

The FastAPI-based REST API provides the following endpoints:

- `/extract-schema`: Extract schema from a database
- `/get-schema`: Get schema for a database
- `/analyze-schema`: Analyze schema using LLM
- `/get-dependencies`: Get dependencies for a database or specific object

### Database Connectors

The system supports the following database types:

- PostgreSQL
- MySQL
- SQL Server
- Sybase

## Frontend Components

The React-based frontend consists of the following components:

- **Dashboard**: Overview of extracted schemas
- **Schema Viewer**: Interactive visualization of database schema
- **Dependency Graph**: Visualization of dependencies between database objects
- **Analysis Panel**: Display of LLM-based analysis results
- **Connection Manager**: Interface for managing database connections

## Deployment Architecture

VMigrateAgent is deployed using Docker and Docker Compose with the following services:

1. **Backend Service**: FastAPI application with the multi-agent system
2. **Frontend Service**: React application for the user interface
3. **Neo4j Service**: Graph database for storing schema data
4. **RabbitMQ Service**: Message broker for agent communication
5. **Sybase Service**: Sybase database for testing and development

## LangGraph Integration

A proof-of-concept integration with LangGraph has been implemented to enhance the agent orchestration system. LangGraph is a framework for building stateful, multi-agent applications with LLMs, providing explicit workflow definitions and improved state management.

### Benefits of LangGraph Integration

1. **Explicit Workflow Definition**: The agent workflow is defined as a directed graph, making it more declarative and easier to understand.
2. **Structured State Management**: Better tracking of the schema extraction process with typed state schemas.
3. **Conditional Branching**: Sophisticated error handling and recovery strategies based on agent outputs.
4. **Parallel Processing Control**: More structured parallel execution patterns for concurrent agent tasks.
5. **Visualization**: Built-in visualization of the workflow graph for better debugging and documentation.
6. **Extensibility**: Simpler process for adding new agents or modifying the workflow.

### LangGraph Workflow Diagram

```
┌─────────────┐         ┌─────────────────┐         ┌─────────────┐         ┌─────────────┐
│ Connection  │─────────▶│    Parallel     │─────────▶│Relationship │─────────▶│ Dependency  │
│   Agent     │         │   Extraction    │         │   Agent     │         │   Agent     │
└─────────────┘         └─────────────────┘         └─────────────┘         └─────────────┘
       │                        │                           │                      │
       ▼                        ▼                           ▼                      ▼
┌─────────────┐         ┌─────────────────┐         ┌─────────────┐         ┌─────────────┐
│   Error     │◀────────│     Error       │◀────────│    Error    │◀────────│    Error    │
│  Handler    │         │    Handler      │         │   Handler   │         │   Handler   │
└─────────────┘         └─────────────────┘         └─────────────┘         └─────────────┘
```

### Implementation

The LangGraph implementation includes:

1. **State Schema Definition**: Typed dictionary defining the structure of the agent workflow state.
2. **Node Implementations**: Each agent is implemented as a node in the graph.
3. **Conditional Routing**: Logic for determining the next step based on agent outputs.
4. **Parallel Execution**: Structured approach for running agents concurrently.

To try the LangGraph orchestrator:

```bash
# Install LangGraph
pip install langgraph>=0.0.19

# Run the comparison example
python src/examples/compare_orchestrators.py
```

The proof-of-concept is available in:
- `src/agents/langgraph_orchestrator.py`: LangGraph-based orchestrator implementation
- `src/examples/compare_orchestrators.py`: Script to compare original and LangGraph orchestrators

## Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/VMigrateAgent.git
   cd VMigrateAgent
   ```

2. Create a `.env` file with your configuration (see Configuration section)

3. Run the Docker Compose setup:
   ```bash
   ./run_docker.sh
   ```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/VMigrateAgent.git
   cd VMigrateAgent
   ```

2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Create a `.env` file with your configuration (see Configuration section)

5. Start the backend:
   ```bash
   python -m src.main api
   ```

6. Start the frontend:
   ```bash
   cd frontend
   npm start
   ```

## Configuration

Create a `.env` file in the root directory with your database connection details:

```
# API Configuration
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret_key

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# Database Configurations
# PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_USER=username
PG_PASSWORD=password
PG_DATABASE=dbname

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=username
MYSQL_PASSWORD=password
MYSQL_DATABASE=dbname

# SQL Server
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_USER=username
MSSQL_PASSWORD=password
MSSQL_DATABASE=dbname

# Sybase
SYBASE_HOST=localhost
SYBASE_PORT=5000
SYBASE_USER=sa
SYBASE_PASSWORD=sybase123
SYBASE_DATABASE=master
```

## Usage

### Command Line Interface

```bash
# Extract schema from a database
python -m src.main extract --connection "postgresql://username:password@localhost:5432/dbname" --output "./output"

# Analyze schema
python -m src.main analyze --database "dbname" --type "dependency" --output "analysis.json"

# Start API server
python -m src.main api --host 0.0.0.0 --port 8000
```

### Python API

```python
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.llm_agent import LLMAgent

# Initialize the orchestrator agent
orchestrator = OrchestratorAgent()

# Extract schema from a database
result = await orchestrator.process({
    "connection_string": "postgresql://username:password@localhost:5432/dbname"
})

schema = result["schema"]

# Initialize LLM agent for analysis
llm_agent = LLMAgent()

# Analyze schema
analysis_result = await llm_agent.process({
    "schema": schema,
    "analysis_type": "dependency"
})
```

## License

MIT
