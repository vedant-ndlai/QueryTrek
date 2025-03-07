# Sybase Database Setup for VMigrateAgent

This guide explains how to set up a Sybase ASE database using Docker for testing the VMigrateAgent multi-agent system.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ with pip
- FreeTDS and ODBC drivers installed

## Setup Instructions

### 1. Install Required Dependencies

First, install the necessary system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y freetds-dev freetds-bin unixodbc unixodbc-dev tdsodbc
```

### 2. Configure ODBC for Sybase

Create or update your ODBC configuration:

```bash
# Add to /etc/odbcinst.ini
sudo bash -c 'cat > /etc/odbcinst.ini << EOL
[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
UsageCount = 1
EOL'

# Add to /etc/odbc.ini
sudo bash -c 'cat > /etc/odbc.ini << EOL
[SYBASE]
Driver = FreeTDS
Description = Sybase ASE
Trace = No
Server = localhost
Port = 5000
Database = SampleDB
TDS_Version = 5.0
EOL'
```

### 3. Start the Docker Containers

Use Docker Compose to start the Sybase container along with Neo4j and RabbitMQ:

```bash
cd /home/kuvedant/VMigrateAgent
docker-compose up -d
```

This will:
- Build and start a Sybase ASE container
- Create a sample database with tables, stored procedures, and relationships
- Start Neo4j for graph storage
- Start RabbitMQ for message queuing

### 4. Verify the Sybase Container

Check if the container is running:

```bash
docker ps | grep vmigrateagent-sybase
```

### 5. Test the Connection

Run the provided test script to verify the connection to Sybase and extract the schema:

```bash
python test_sybase_connection.py
```

## Sample Database Structure

The sample database includes:

### Schemas
- `sales` - Sales-related tables and procedures
- `inventory` - Inventory management tables and procedures
- `hr` - Human resources tables and procedures

### Tables
- `sales.customers` - Customer information
- `sales.orders` - Order headers
- `sales.order_items` - Order line items
- `inventory.products` - Product catalog
- `inventory.suppliers` - Supplier information
- `inventory.inventory_transactions` - Inventory movements
- `hr.employees` - Employee information

### Views
- `sales.customer_orders` - Customer order summary
- `inventory.product_inventory` - Product inventory with supplier details
- `sales.order_details` - Detailed order information

### Stored Procedures
- `sales.create_order` - Create a new order
- `sales.add_order_item` - Add an item to an order
- `inventory.update_product_stock` - Update product inventory
- `hr.get_employee_hierarchy` - Get employee reporting structure

### Functions
- `sales.calculate_order_total` - Calculate the total for an order
- `inventory.get_product_value` - Calculate inventory value

### Triggers
- `sales.trg_update_order_total` - Update order totals when items change
- `inventory.trg_update_product_timestamp` - Update timestamp when products change

## Using with VMigrateAgent

To extract the schema using the VMigrateAgent:

```bash
python -m src.main extract --connection "DRIVER={FreeTDS};SERVER=localhost;PORT=5000;DATABASE=SampleDB;UID=sa;PWD=sybase123;TDS_VERSION=5.0"
```

To analyze the schema:

```bash
python -m src.main analyze --database "SampleDB" --type dependency
```

To start the API server:

```bash
python -m src.main api
```

## Accessing Neo4j and RabbitMQ

- Neo4j browser: http://localhost:7474 (username: neo4j, password: password)
- RabbitMQ management: http://localhost:15672 (username: guest, password: guest)

## Troubleshooting

If you encounter connection issues:

1. Ensure the Sybase container is running:
   ```bash
   docker logs vmigrateagent-sybase
   ```

2. Check if the database initialization completed:
   ```bash
   docker exec -it vmigrateagent-sybase bash -c "isql -Usa -Psybase123 -SSYBASE -i /dev/stdin <<< 'SELECT name FROM master..sysdatabases'"
   ```

3. Verify FreeTDS configuration:
   ```bash
   tsql -H localhost -p 5000 -U sa -P sybase123
   ```
