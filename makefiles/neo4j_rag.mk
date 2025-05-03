# Neo4j RAG integration commands

# Start Neo4j container
neo4j-start: env-setup
	@echo "Starting Neo4j container..."
	. .venv/bin/activate && . .env && docker-compose -f docker-compose.neo4j.yml up -d

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
	. .venv/bin/activate && . .env && pytest tests/database/test_neo4j_connector.py tests/extensions/test_neo4j_prompt_generator.py tests/extensions/test_neo4j_query_generator.py $(ARGS)

# Open Neo4j browser UI
neo4j-browser:
	@echo "Opening Neo4j browser UI..."
	open http://localhost:7474

# Run Neo4j connection health check
neo4j-health: env-setup
	@echo "Checking Neo4j connection health..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_rag_demo.py health-check $(ARGS)

# Embed Neo4j schema information
neo4j-embed-schema: env-setup
	@echo "Embedding Neo4j schema information..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_rag_demo.py schema --embed $(ARGS)

# Search Neo4j schema
neo4j-search-schema: env-setup
	@echo "Searching Neo4j schema..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_rag_demo.py schema --query "$(QUERY)" $(ARGS)

# Search Neo4j documents
neo4j-search-docs: env-setup
	@echo "Searching Neo4j documents..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_rag_demo.py documents --query "$(QUERY)" $(ARGS)

# Generate and execute Cypher query from natural language
neo4j-nl-query: env-setup
	@echo "Generating and executing Cypher query from natural language..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_rag_demo.py cypher --nl-query "$(QUERY)" $(ARGS)

# Execute specific Cypher query
neo4j-query: env-setup
	@echo "Executing Cypher query..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_rag_demo.py cypher --query "$(QUERY)" $(ARGS)

# Run comprehensive Neo4j RAG demo
neo4j-rag-demo: env-setup
	@echo "Running comprehensive Neo4j RAG demo..."
	. .venv/bin/activate && . .env && PYTHONPATH=. python commands/neo4j_rag_demo.py rag --query "$(QUERY)" $(ARGS)

# Install Neo4j Python driver and dependencies
neo4j-install: env-setup
	@echo "Installing Neo4j dependencies..."
	. .venv/bin/activate && pip install neo4j pyarrow faiss-cpu

# Setup complete Neo4j RAG environment
neo4j-setup: neo4j-install neo4j-start neo4j-seed neo4j-embed-schema
	@echo "Neo4j RAG environment setup complete" 