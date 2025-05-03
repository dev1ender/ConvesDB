# Neo4j database integration commands

# Start Neo4j container
neo4j-start: env-setup
	@echo "Starting Neo4j container..."
	. .venv/bin/activate && . .env && ./scripts/start_neo4j.sh

# Stop Neo4j container
neo4j-stop:
	@echo "Stopping Neo4j container..."
	docker-compose -f docker-compose.neo4j.yml down

# Seed Neo4j with test data
neo4j-seed: env-setup
	@echo "Seeding Neo4j with test data..."
	. .venv/bin/activate && . .env && python scripts/seed_neo4j.py $(ARGS)

# Seed Neo4j with large-scale realistic data
neo4j-seed-large: env-setup
	@echo "Seeding Neo4j with large-scale data..."
	. .venv/bin/activate && . .env && python scripts/seed_neo4j_large.py $(ARGS)

# Run Neo4j integration tests
neo4j-test: env-setup
	@echo "Running Neo4j integration tests..."
	. .venv/bin/activate && . .env && pytest tests/database/test_neo4j_connector.py tests/store/test_neo4j_document_store.py $(ARGS)

# Open Neo4j browser UI
neo4j-browser:
	@echo "Opening Neo4j browser UI..."
	open http://localhost:7474

# Embed Neo4j schema information
neo4j-embed-schema: env-setup
	@echo "Embedding Neo4j schema information..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_demo.py embed-schema

# Run Neo4j document search demo
neo4j-search: env-setup
	@echo "Running Neo4j document search demo..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_demo.py $(ARGS)

# Generate embeddings for Neo4j nodes
neo4j-embed: env-setup
	@echo "Generating embeddings for Neo4j nodes..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_demo.py generate-embeddings $(ARGS)

# Run comprehensive Neo4j demo
neo4j-demo: env-setup
	@echo "Running comprehensive Neo4j demo..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_demo.py demo $(ARGS) 