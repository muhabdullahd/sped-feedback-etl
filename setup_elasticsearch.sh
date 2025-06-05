#!/bin/zsh
# Setup script for Elasticsearch for the SPED Feedback ETL System

set -e  # Exit on error

# Terminal colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print section header
print_header() {
    echo ""
    echo "${BLUE}============================================================${NC}"
    echo "${BLUE}  $1${NC}"
    echo "${BLUE}============================================================${NC}"
    echo ""
}

# Print success message
print_success() {
    echo "${GREEN}✓ $1${NC}"
}

# Print info message
print_info() {
    echo "${YELLOW}➜ $1${NC}"
}

# Print error message
print_error() {
    echo "${RED}✗ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
        exit 1
    else
        print_success "Docker is installed."
    fi
}

# Check if the Elasticsearch container is already running
check_elasticsearch_running() {
    if docker ps | grep -q "elasticsearch"; then
        print_success "Elasticsearch is already running."
        return 0
    else
        return 1
    fi
}

# Start Elasticsearch
start_elasticsearch() {
    print_info "Starting Elasticsearch..."
    
    # Create a docker network if it doesn't exist
    if ! docker network ls | grep -q "sped-network"; then
        docker network create sped-network
        print_success "Created Docker network: sped-network"
    fi
    
    # Start Elasticsearch
    docker run -d \
        --name elasticsearch \
        --network sped-network \
        -p 9200:9200 \
        -p 9300:9300 \
        -e "discovery.type=single-node" \
        -e "xpack.security.enabled=false" \
        docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    
    print_success "Started Elasticsearch container."
    
    # Wait for Elasticsearch to be ready
    print_info "Waiting for Elasticsearch to be ready..."
    until $(curl --output /dev/null --silent --head --fail http://localhost:9200); do
        printf '.'
        sleep 2
    done
    
    print_success "Elasticsearch is now ready at http://localhost:9200"
}

# Main function
main() {
    print_header "Setting up Elasticsearch for SPED Feedback ETL System"
    
    # Check if Docker is installed
    check_docker
    
    # Check if Elasticsearch is already running
    if ! check_elasticsearch_running; then
        start_elasticsearch
    fi
    
    # Set environment variables
    print_info "Setting Elasticsearch environment variables..."
    export ELASTICSEARCH_HOST=localhost
    export ELASTICSEARCH_PORT=9200
    
    # Add environment variables to .env file if it exists
    if [ -f .env ]; then
        # Check if variables already exist in .env
        if ! grep -q "ELASTICSEARCH_HOST" .env; then
            echo "ELASTICSEARCH_HOST=localhost" >> .env
            echo "ELASTICSEARCH_PORT=9200" >> .env
            print_success "Added Elasticsearch environment variables to .env file."
        else
            print_info "Elasticsearch environment variables already exist in .env file."
        fi
    else
        # Create .env file with Elasticsearch variables
        echo "ELASTICSEARCH_HOST=localhost" > .env
        echo "ELASTICSEARCH_PORT=9200" >> .env
        print_success "Created .env file with Elasticsearch environment variables."
    fi
    
    print_header "Elasticsearch Setup Complete"
    print_info "Elasticsearch is running at http://localhost:9200"
    print_info "To stop Elasticsearch, run: docker stop elasticsearch"
    print_info "To remove the Elasticsearch container, run: docker rm elasticsearch"
}

# Run the main function
main
