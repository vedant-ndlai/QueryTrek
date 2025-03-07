# VMigrateAgent: Multi-Agent Database Schema Extraction System

A scalable, multi-agent system that dynamically extracts database schemas from various relational databases (PostgreSQL, MySQL, SQL Server, Sybase).

## Features

- Dynamic database type detection
- Schema metadata extraction
- Dependency analysis between database objects
- Specialized agents for different aspects of schema extraction:
  - Table extraction
  - Foreign key mapping
  - Stored procedure parsing
  - Dependency resolution

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the root directory with your database connection details:

```
# Example for PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_USER=username
PG_PASSWORD=password
PG_DATABASE=dbname

# Example for MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=username
MYSQL_PASSWORD=password
MYSQL_DATABASE=dbname

# Example for SQL Server
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_USER=username
MSSQL_PASSWORD=password
MSSQL_DATABASE=dbname
```

## Usage

```python
from vmigrateagent import SchemaExtractor

# Initialize the schema extractor
extractor = SchemaExtractor()

# Extract schema from a database
schema = extractor.extract("postgresql://username:password@localhost:5432/dbname")

# Analyze dependencies
dependencies = extractor.analyze_dependencies(schema)

# Export schema to JSON
extractor.export_to_json(schema, "schema.json")
```

## Architecture

The system uses a multi-agent architecture where specialized agents handle different aspects of the schema extraction process:

1. **Coordinator Agent**: Orchestrates the overall extraction process
2. **Connection Agent**: Handles database connections and type detection
3. **Table Agent**: Extracts table definitions and columns
4. **Relationship Agent**: Maps foreign keys and table relationships
5. **Procedure Agent**: Parses stored procedures and functions
6. **Dependency Agent**: Analyzes dependencies between database objects

## License

MIT
