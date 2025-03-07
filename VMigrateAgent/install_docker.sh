#!/bin/bash
# Script to install Docker and Docker Compose

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

# Check if Docker is already installed
print_header "Checking for Existing Docker Installation"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is already installed${NC}"
    docker --version
    DOCKER_INSTALLED=true
else
    echo -e "${YELLOW}Docker is not installed. Proceeding with installation...${NC}"
    DOCKER_INSTALLED=false
fi

# Check if Docker Compose is already installed
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose is already installed${NC}"
    docker-compose --version
    COMPOSE_INSTALLED=true
else
    echo -e "${YELLOW}Docker Compose is not installed. Proceeding with installation...${NC}"
    COMPOSE_INSTALLED=false
fi

# Install Docker if not already installed
if [ "$DOCKER_INSTALLED" = false ]; then
    print_header "Installing Docker"
    
    # Update package index
    echo -e "${YELLOW}Updating package index...${NC}"
    sudo apt-get update
    check_status "Updated package index"
    
    # Install prerequisites
    echo -e "${YELLOW}Installing prerequisites...${NC}"
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg
    check_status "Installed prerequisites"
    
    # Add Docker's official GPG key
    echo -e "${YELLOW}Adding Docker's GPG key...${NC}"
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    check_status "Added Docker's GPG key"
    
    # Set up the stable repository
    echo -e "${YELLOW}Setting up Docker repository...${NC}"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    check_status "Set up Docker repository"
    
    # Update package index again
    echo -e "${YELLOW}Updating package index with Docker repository...${NC}"
    sudo apt-get update
    check_status "Updated package index"
    
    # Install Docker Engine
    echo -e "${YELLOW}Installing Docker Engine...${NC}"
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    check_status "Installed Docker Engine" "exit"
    
    # Start and enable Docker service
    echo -e "${YELLOW}Starting Docker service...${NC}"
    sudo systemctl start docker
    sudo systemctl enable docker
    check_status "Started Docker service"
    
    # Add current user to docker group
    echo -e "${YELLOW}Adding current user to docker group...${NC}"
    sudo usermod -aG docker $USER
    check_status "Added current user to docker group"
    
    echo -e "${GREEN}✓ Docker installed successfully${NC}"
    docker --version
fi

# Install Docker Compose if not already installed
if [ "$COMPOSE_INSTALLED" = false ]; then
    print_header "Installing Docker Compose"
    
    # Install Docker Compose
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    check_status "Downloaded Docker Compose"
    
    # Apply executable permissions
    sudo chmod +x /usr/local/bin/docker-compose
    check_status "Applied executable permissions"
    
    echo -e "${GREEN}✓ Docker Compose installed successfully${NC}"
    docker-compose --version
fi

# Verify installations
print_header "Verifying Installations"
echo -e "${YELLOW}Verifying Docker installation...${NC}"
docker --version
check_status "Docker is installed and functioning"

echo -e "${YELLOW}Verifying Docker Compose installation...${NC}"
docker-compose --version
check_status "Docker Compose is installed and functioning"

# Test Docker
echo -e "${YELLOW}Testing Docker with hello-world container...${NC}"
docker run --rm hello-world
check_status "Docker test successful"

# Print notice about group membership
print_header "Important Notice"
echo -e "${YELLOW}To use Docker without sudo, you need to log out and log back in for the group membership to take effect.${NC}"
echo -e "${YELLOW}Alternatively, you can run the following command to activate the changes to groups:${NC}"
echo -e "${BLUE}newgrp docker${NC}"

# Print summary
print_header "Installation Summary"
echo -e "${GREEN}✓ Docker installed and configured${NC}"
echo -e "${GREEN}✓ Docker Compose installed and configured${NC}"
echo -e "${GREEN}✓ Current user added to docker group${NC}"

echo -e "\n${GREEN}Docker installation completed successfully!${NC}"
