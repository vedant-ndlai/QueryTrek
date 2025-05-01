# QueryTreck: Multi-Agent Database Migration and Modernization Platform

## Project Overview

QueryTreck is a comprehensive, AI-powered platform designed to simplify and accelerate database migration and modernization processes. Built on a multi-agent architecture, it leverages advanced AI techniques to extract, analyze, and transform database schemas and queries across different database systems.


QueryTreck aims to solve the following challenges in database migration and modernization:

1. **Reduce Migration Complexity**: Simplify the process of migrating from legacy database systems to modern cloud-based solutions.

2. **Automate Schema Extraction**: Automatically extract and analyze database schemas from various relational databases (PostgreSQL, MySQL, SQL Server, Sybase).

3. **Intelligent Query Conversion**: Transform SQL queries from one dialect to another with high accuracy using AI-powered agents.

4. **Dependency Analysis**: Identify and visualize complex dependencies between database objects to facilitate migration planning.

5. **Performance Optimization**: Provide recommendations for optimizing database performance during and after migration.

6. **Collaborative Workflow**: Enable teams to collaborate effectively during the migration process with a modern web interface.


## Key Features

- **Dynamic Database Type Detection**: Automatically identify and connect to different database types
- **Comprehensive Schema Extraction**: Extract tables, views, stored procedures, and relationships
- **Intelligent Query Transformation**: Convert queries between different SQL dialects
- **Dependency Visualization**: Interactive visualization of database object dependencies
- **Multi-Agent Architecture**: Specialized AI agents for different aspects of migration
- **Modern Web Interface**: Intuitive React-based UI for managing migration projects
- **Authentication System**: Secure user authentication and authorization
- **RESTful API**: Well-documented API for integration with other systems
- **Docker-based Deployment**: Easy deployment using containerization

## System Architecture

### Architecture Overview

QueryTreck follows a microservices-based architecture with the following key components:

1. **Multi-Agent Backend System**: Core system with specialized agents for different tasks
2. **Neo4j Graph Database**: Stores extracted schema data and relationships
3. **RabbitMQ Message Broker**: Handles asynchronous communication between agents
4. **FastAPI REST API**: Provides external access to the system
5. **React Frontend**: User interface for interacting with the system
6. **Database Connectors**: Adapters for different database systems


### Azure-Based Architecture

When deployed on Microsoft Azure, QueryTreck leverages the following Azure services:

![Architecture Diagram](https://drive.google.com/file/d/1SNmffmggLOCm4SSoxnwaPSUqidr0cBfb/view?usp=drive_link)


```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Azure Architecture                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Azure App Service                                │
│                                                                             │
│  ┌───────────────────┐       ┌───────────────────┐                          │
│  │   Frontend App    │       │    Backend API    │                          │
│  │    (React SPA)    │◄─────►│    (FastAPI)      │                          │
│  └───────────────────┘       └─────────┬─────────┘                          │
│                                        │                                     │
└────────────────────────────────────────┼─────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          Azure Kubernetes Service                           │
│                                                                            │
│  ┌───────────────────┐       ┌───────────────────┐      ┌───────────────┐  │
│  │  Orchestrator     │       │  Connection       │      │  Table        │  │
│  │  Agent            │◄─────►│  Agent            │◄────►│  Agent        │  │
│  └───────────────────┘       └───────────────────┘      └───────────────┘  │
│                                                                            │
│  ┌───────────────────┐       ┌───────────────────┐      ┌───────────────┐  │
│  │  Procedure        │       │  Relationship     │      │  Dependency   │  │
│  │  Agent            │◄─────►│  Agent            │◄────►│  Agent        │  │
│  └───────────────────┘       └───────────────────┘      └───────────────┘  │
│                                                                            │
│  ┌───────────────────┐       ┌───────────────────┐      ┌───────────────┐  │
│  │  LLM              │       │  Graph            │      │  Code         │  │
│  │  Agent            │◄─────►│  Agent            │◄────►│  Converter    │  │
│  └───────────────────┘       └───────────────────┘      └───────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                │                    │                     │
                ▼                    ▼                     ▼
┌───────────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐
│  Azure Cosmos DB      │  │  Azure Service   │  │  Azure OpenAI Service    │
│  (Neo4j API)          │  │  Bus             │  │                          │
└───────────────────────┘  └──────────────────┘  └──────────────────────────┘
                │                                              │
                ▼                                              ▼
┌───────────────────────┐                         ┌───────────────────────────┐
│  Azure Cache for      │                         │  Azure Cognitive Search   │
│  Redis                │                         │                           │
└───────────────────────┘                         └───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Azure SQL Database                              │
│                                                                             │
│  ┌───────────────────┐       ┌───────────────────┐      ┌───────────────┐   │
│  │   User Data &     │       │  Migration        │      │  Schema       │   │
│  │   Authentication  │       │  Projects         │      │  Cache        │   │
│  └───────────────────┘       └───────────────────┘      └───────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Azure Key Vault                                    │
│                                                                             │
│  ┌───────────────────┐       ┌───────────────────┐      ┌───────────────┐   │
│  │   API Keys        │       │  Database         │      │  Service      │   │
│  │                   │       │  Credentials      │      │  Principals   │   │
│  └───────────────────┘       └───────────────────┘      └───────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

The following diagram illustrates the key components of the QueryTreck system and their interactions:

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
   - Frontend sends the request to the FastAPI backend

2. **Connection and Extraction**:
   - Orchestrator Agent receives the request and initializes the extraction process
   - Connection Agent establishes connection to the source database
   - Table Agent extracts table definitions
   - Relationship Agent extracts foreign key relationships
   - Procedure Agent extracts stored procedures and functions
   - Dependency Agent analyzes dependencies between objects

3. **Data Storage and Processing**:
   - Extracted schema is stored in Neo4j graph database
   - Graph Agent manages the graph representation of the schema
   - LLM Agent performs intelligent analysis using language models

4. **Results and Visualization**:
   - Results are sent back to the frontend
   - Frontend displays the schema, dependencies, and analysis results
   - User can interact with the visualization and perform further actions

## Technology Stack

### Backend
- **Python 3.9+**: Core programming language
- **FastAPI**: High-performance web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Neo4j**: Graph database for storing schema relationships
- **RabbitMQ**: Message broker for agent communication
- **OpenAI API**: For LLM-based analysis and code conversion
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server
- **Docker & Docker Compose**: Containerization

### Frontend
- **React**: JavaScript library for building user interfaces
- **TypeScript**: Typed JavaScript
- **Material-UI**: React component library
- **React Router**: Navigation and routing
- **Axios**: HTTP client
- **Cytoscape.js**: Graph visualization library
- **React Query**: Data fetching and state management
- **JWT Authentication**: Secure user authentication

### Database Connectors
- **psycopg2**: PostgreSQL connector
- **pymysql**: MySQL connector
- **pyodbc**: SQL Server and Sybase connector
- **aiosqlite**: Async SQLite connector

## Components

### Backend Components

#### Agent System
The core of QueryTreck is its multi-agent system, where each agent specializes in a specific task:

1. **Orchestrator Agent**: Coordinates the entire extraction and analysis process
2. **Connection Agent**: Handles database connections and type detection
3. **Table Agent**: Extracts table definitions and column metadata
4. **Relationship Agent**: Extracts foreign key relationships
5. **Procedure Agent**: Extracts and parses stored procedures
6. **Dependency Agent**: Analyzes dependencies between database objects
7. **Graph Agent**: Manages the Neo4j graph representation of the schema
8. **LLM Agent**: Performs intelligent analysis using language models
9. **Code Converter Agent**: Transforms SQL queries between different dialects

#### API Layer
The FastAPI-based REST API provides endpoints for:
- User authentication and management
- Database connection management
- Schema extraction and analysis
- Query conversion
- Dependency analysis

#### Database Models
The system uses Pydantic models to represent database objects:
- `DatabaseSchema`: Top-level container for all schema objects
- `Table`: Represents database tables
- `Column`: Represents table columns
- `ForeignKey`: Represents foreign key relationships
- `StoredProcedure`: Represents stored procedures and functions
- `View`: Represents database views
- `Trigger`: Represents database triggers
- `Dependency`: Represents dependencies between objects

### Frontend Components

#### Pages
- **Landing Page**: Introduction and sign-up/login
- **Dashboard**: Overview of projects and recent activities
- **Connection Form**: Interface for connecting to databases
- **Schema Viewer**: Visualization of database schema
- **Dependency Analysis**: Interactive dependency graph
- **Code Converter**: Interface for converting SQL queries
- **Settings**: User and application settings

#### Components
- **Authentication**: User login, signup, and session management
- **Navigation**: App-wide navigation and routing
- **Schema Graph**: Interactive visualization of database schema
- **Dependency Graph**: Interactive visualization of object dependencies
- **Query Editor**: SQL editor with syntax highlighting
- **Results Viewer**: Display of query results and analysis

## Deployment Guide

QueryTreck can be deployed in various environments, including local development, on-premises servers, and cloud platforms like Azure.

### Azure Deployment

To deploy QueryTreck on Azure:

1. **Prerequisites**:
   - Azure subscription
   - Azure CLI installed
   - Docker and Docker Compose installed

2. **Azure Resources**:
   - Azure App Service for frontend and backend
   - Azure Kubernetes Service for agent system
   - Azure Cosmos DB with Neo4j API for graph database
   - Azure Service Bus for message queuing
   - Azure SQL Database for user data
   - Azure OpenAI Service for LLM capabilities
   - Azure Key Vault for secrets management

3. **Deployment Steps**:
   - Provision required Azure resources
   - Configure environment variables and secrets
   - Build and push Docker images to Azure Container Registry
   - Deploy containers to Azure Kubernetes Service
   - Configure networking and security
   - Set up monitoring and logging

## Security Considerations

QueryTreck implements several security measures:

1. **Authentication**: JWT-based authentication with secure password hashing
2. **Authorization**: Role-based access control for different user types
3. **Data Protection**: Encryption of sensitive data at rest and in transit
4. **Secrets Management**: Secure storage of credentials and API keys
5. **Input Validation**: Thorough validation of all user inputs
6. **Dependency Scanning**: Regular scanning for vulnerabilities in dependencies
7. **Secure Deployment**: Containerization and isolation of components

## Future Roadmap

Planned enhancements for QueryTreck include:

1. **Advanced AI Features**: Enhanced query optimization and schema recommendations
2. **Collaborative Features**: Real-time collaboration for team-based migrations
3. **Integration with DevOps Tools**: CI/CD pipeline integration
4. **Performance Benchmarking**: Tools for comparing performance before and after migration
5. **Compliance Checking**: Validation against industry standards and best practices
6. **Multi-tenant Support**: Enhanced support for SaaS deployment model

---

© 2025 QueryTreck. All rights reserved.
