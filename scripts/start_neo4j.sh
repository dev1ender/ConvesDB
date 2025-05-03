#!/bin/bash

# Start Neo4j using Docker Compose
echo "Starting Neo4j database..."

# Create directories if they don't exist
mkdir -p ./licenses
mkdir -p ./scripts/neo4j

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose is not installed. Please install it to continue."
    exit 1
fi

# Check if license file exists (for enterprise features)
if [ ! -f "./licenses/gds.license" ]; then
    echo "Warning: No GDS license file found in ./licenses/gds.license"
    echo "For production use, obtain a Graph Data Science license from Neo4j"
    echo "For development, we'll continue without vector search capabilities"
    
    # Create directory for license files
    mkdir -p "./licenses"
    # Create empty file to avoid Docker errors
    touch "./licenses/gds.license"
fi

# Start Neo4j container
docker-compose -f docker-compose.neo4j.yml up -d

# Wait for Neo4j to start
echo "Waiting for Neo4j to start..."
sleep 10

# Check if Neo4j is running
if docker ps | grep -q "rag-neo4j"; then
    echo "Neo4j is running."
    echo "Neo4j Browser: http://localhost:7474/"
    echo "Username: neo4j"
    echo "Password: password"
    echo ""
    echo "To stop Neo4j: docker-compose -f docker-compose.neo4j.yml down"
else
    echo "Failed to start Neo4j. Check docker logs for details:"
    echo "docker logs rag-neo4j"
fi 