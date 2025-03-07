#!/bin/bash
# Script to build and run the VMigrateAgent system in Docker

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
print_header "Checking Environment Variables"
if [ -z "${OPENAI_API_KEY}" ]; then
    echo -e "${YELLOW}OPENAI_API_KEY environment variable is not set.${NC}"
    echo -e "${YELLOW}Please enter your OpenAI API key (or press Enter to skip):${NC}"
    read api_key
    
    if [ -n "$api_key" ]; then
        export OPENAI_API_KEY=$api_key
        echo -e "${GREEN}✓ OPENAI_API_KEY has been set for this session${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: OPENAI_API_KEY not set. LLM Agent functionality will be limited.${NC}"
    fi
else
    echo -e "${GREEN}✓ OPENAI_API_KEY is set${NC}"
fi

# Build and start the containers
print_header "Building and Starting Docker Containers"
echo -e "${YELLOW}Building and starting containers (this may take a few minutes)...${NC}"
sudo docker-compose up --build -d
check_status "Started all containers" "exit"

# Wait for services to be ready
print_header "Waiting for Services to Start"
echo -e "${YELLOW}Waiting for services to be ready (this may take a few minutes)...${NC}"

# Function to check if a service is ready
check_service() {
    local service=$1
    local max_attempts=$2
    local attempt=1
    
    echo -e "${YELLOW}Checking $service...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if sudo docker ps | grep -q "vmigrateagent-$service" && sudo docker ps | grep "vmigrateagent-$service" | grep -q "Up"; then
            echo -e "${GREEN}✓ $service is running${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: Waiting for $service...${NC}"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}✗ $service failed to start after $max_attempts attempts${NC}"
    return 1
}

# Check each service
check_service "sybase" 12
check_service "neo4j" 6
check_service "rabbitmq" 6
check_service "backend" 6
check_service "frontend" 6

# Print access information
print_header "Access Information"
echo -e "${GREEN}All services are up and running!${NC}"
echo -e "\n${YELLOW}You can access the following services:${NC}"
echo -e "- Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "- Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "- Neo4j Browser: ${BLUE}http://localhost:7474${NC} (username: neo4j, password: password)"
echo -e "- RabbitMQ Management: ${BLUE}http://localhost:15672${NC} (username: guest, password: guest)"

# Print helpful commands
print_header "Helpful Commands"
echo -e "${YELLOW}To view logs for a specific service:${NC}"
echo -e "${BLUE}sudo docker-compose logs -f <service>${NC}"
echo -e "Example: ${BLUE}sudo docker-compose logs -f backend${NC}"

echo -e "\n${YELLOW}To stop all services:${NC}"
echo -e "${BLUE}sudo docker-compose down${NC}"

echo -e "\n${YELLOW}To restart a specific service:${NC}"
echo -e "${BLUE}sudo docker-compose restart <service>${NC}"
echo -e "Example: ${BLUE}sudo docker-compose restart frontend${NC}"

echo -e "\n${GREEN}System is ready for testing!${NC}"
