# Main Makefile for conversDB application
# This file includes all component makefiles from the makefiles directory

.PHONY: all setup install install-test setup-ollama setup-llama-local run-cli run-api run-ui run-demo test \
        test-embeddings test-validation-modes clean config-openai config-ollama config-huggingface config-local-llama \
        env-setup schema-extract schema-enrich schema-embed schema-docs schema-pure \
        help check-ollama env run-demo-config run-demo-questions test-nlsql \
        pytest test-api test-db test-db-integration test-postgres test-all-db test-all \
        neo4j-start neo4j-stop neo4j-seed neo4j-seed-large neo4j-test neo4j-browser \
        neo4j-embed-schema neo4j-search neo4j-embed \
        neo4j-health neo4j-search-schema neo4j-search-docs neo4j-nl-query neo4j-query \
        neo4j-rag-demo neo4j-install neo4j-setup

# Include component makefiles
include makefiles/setup.mk
include makefiles/run.mk
include makefiles/test.mk
include makefiles/config.mk
include makefiles/schema.mk
include makefiles/neo4j.mk
include makefiles/neo4j_rag.mk
include makefiles/help.mk

# Default target
all: setup

run-main:
	python3 -m app.main
