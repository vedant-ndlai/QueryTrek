#!/bin/bash
# Script to build and run the VMigrateAgent system in Docker step by step

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}   $1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

# Function to check if a command was successful
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success: $1${NC}"
    else
        echo -e "${RED}✗ Error: $1${NC}"
        if [ "$2" = "exit" ]; then
            exit 1
        fi
    fi
}

# Check if Docker is installed
print_header "Checking Prerequisites"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please run ./install_docker.sh first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please run ./install_docker.sh first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check for OpenAI API key
print_header "Setting Environment Variables"
if [ -z "${OPENAI_API_KEY}" ]; then
    echo -e "${YELLOW}OPENAI_API_KEY environment variable is not set.${NC}"
    echo -e "${YELLOW}Please enter your OpenAI API key (or press Enter to skip):${NC}"
    read api_key
    
    if [ -n "$api_key" ]; then
        export OPENAI_API_KEY=$api_key
        echo -e "${GREEN}✓ OPENAI_API_KEY has been set for this session${NC}"
        
        # Save to .env file for docker-compose
        echo "OPENAI_API_KEY=$api_key" > .env
        echo -e "${GREEN}✓ Created .env file with API key for docker-compose${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: OPENAI_API_KEY not set. LLM Agent functionality will be limited.${NC}"
        echo "OPENAI_API_KEY=" > .env
    fi
else
    echo -e "${GREEN}✓ OPENAI_API_KEY is set${NC}"
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" > .env
    echo -e "${GREEN}✓ Created .env file with API key for docker-compose${NC}"
fi

# Step 1: Build and start RabbitMQ
print_header "Step 1: Building and Starting RabbitMQ"
echo -e "${YELLOW}Starting RabbitMQ...${NC}"
sudo docker-compose up -d rabbitmq
check_status "Started RabbitMQ"

# Wait for RabbitMQ to be ready
echo -e "${YELLOW}Waiting for RabbitMQ to be ready...${NC}"
sleep 15
sudo docker-compose ps rabbitmq | grep "Up" > /dev/null
check_status "RabbitMQ is running"

# Step 2: Build and start Neo4j
print_header "Step 2: Building and Starting Neo4j"
echo -e "${YELLOW}Starting Neo4j...${NC}"
sudo docker-compose up -d neo4j
check_status "Started Neo4j"

# Wait for Neo4j to be ready
echo -e "${YELLOW}Waiting for Neo4j to be ready...${NC}"
sleep 15
sudo docker-compose ps neo4j | grep "Up" > /dev/null
check_status "Neo4j is running"

# Step 3: Build and start Sybase
print_header "Step 3: Building and Starting Sybase"
echo -e "${YELLOW}Building and starting Sybase (this may take a while)...${NC}"
sudo docker-compose up -d --build sybase
check_status "Started Sybase build"

echo -e "${YELLOW}Sybase build is running in the background. This may take several minutes.${NC}"
echo -e "${YELLOW}You can check the status with: sudo docker-compose ps sybase${NC}"
echo -e "${YELLOW}Let's continue with the next steps while Sybase builds...${NC}"

# Step 4: Build the backend
print_header "Step 4: Building Backend"
echo -e "${YELLOW}Building backend...${NC}"
sudo docker-compose build backend
check_status "Built backend"

# Step 5: Build the frontend
print_header "Step 5: Building Frontend"
echo -e "${YELLOW}Building frontend...${NC}"
sudo docker-compose build frontend
check_status "Built frontend"

# Step 6: Start the backend and frontend
print_header "Step 6: Starting Backend and Frontend"
echo -e "${YELLOW}Starting backend and frontend...${NC}"
sudo docker-compose up -d backend frontend
check_status "Started backend and frontend"

# Print access information
print_header "Access Information"
echo -e "${GREEN}Services are starting up!${NC}"
echo -e "\n${YELLOW}You can access the following services:${NC}"
echo -e "- Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "- Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "- Neo4j Browser: ${BLUE}http://localhost:7474${NC} (username: neo4j, password: password)"
echo -e "- RabbitMQ Management: ${BLUE}http://localhost:15672${NC} (username: guest, password: guest)"

# Print helpful commands
print_header "Helpful Commands"
echo -e "${YELLOW}To check the status of all services:${NC}"
echo -e "${BLUE}sudo docker-compose ps${NC}"

echo -e "\n${YELLOW}To view logs for a specific service:${NC}"
echo -e "${BLUE}sudo docker-compose logs -f <service>${NC}"
echo -e "Example: ${BLUE}sudo docker-compose logs -f backend${NC}"

echo -e "\n${YELLOW}To stop all services:${NC}"
echo -e "${BLUE}sudo docker-compose down${NC}"

echo -e "\n${YELLOW}To restart a specific service:${NC}"
echo -e "${BLUE}sudo docker-compose restart <service>${NC}"
echo -e "Example: ${BLUE}sudo docker-compose restart frontend${NC}"

echo -e "\n${GREEN}Build process has been started!${NC}"
echo -e "${YELLOW}Note: Sybase may still be building in the background. Check its status with:${NC}"
echo -e "${BLUE}sudo docker-compose ps sybase${NC}"
