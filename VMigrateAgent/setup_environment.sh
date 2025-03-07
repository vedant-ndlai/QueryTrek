#!/bin/bash
# Script to set up Python virtual environment and install dependencies

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

# Check if Python is installed
print_header "Checking Prerequisites"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

python_version=$(python3 --version)
echo -e "${GREEN}✓ $python_version is installed${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}Installing pip...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3-pip
    check_status "Installed pip" "exit"
else
    echo -e "${GREEN}✓ pip is installed${NC}"
fi

# Check if venv module is installed
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${YELLOW}Installing venv module...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3-venv
    check_status "Installed venv module" "exit"
else
    echo -e "${GREEN}✓ venv module is installed${NC}"
fi

# Create virtual environment
print_header "Creating Virtual Environment"
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
check_status "Created virtual environment" "exit"

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
check_status "Activated virtual environment" "exit"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip
check_status "Upgraded pip"

# Install dependencies
print_header "Installing Dependencies"
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt
check_status "Installed requirements"

# Install additional dependencies for database connectivity
print_header "Installing Database Connectivity Packages"
echo -e "${YELLOW}Installing database connectivity packages...${NC}"
pip install pyodbc sqlalchemy pymysql psycopg2-binary
check_status "Installed database connectivity packages"

# Install development tools
print_header "Installing Development Tools"
echo -e "${YELLOW}Installing development tools...${NC}"
pip install pytest pytest-asyncio black isort mypy
check_status "Installed development tools"

# Print summary
print_header "Setup Summary"
echo -e "${GREEN}✓ Python virtual environment created and activated${NC}"
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo -e "${GREEN}✓ Database connectivity packages installed${NC}"
echo -e "${GREEN}✓ Development tools installed${NC}"

echo -e "\n${YELLOW}To activate the virtual environment in the future, run:${NC}"
echo -e "${BLUE}source venv/bin/activate${NC}"

echo -e "\n${YELLOW}To deactivate the virtual environment, run:${NC}"
echo -e "${BLUE}deactivate${NC}"

echo -e "\n${GREEN}Environment setup completed successfully!${NC}"
