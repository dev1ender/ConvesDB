# Schema related tasks

# Extract schema from database
schema-extract: env-setup
	@echo "Extracting database schema..."
	@mkdir -p schema
	. .venv/bin/activate && . .env && python app/schema_extractor.py --db example.sqlite --output-dir schema --output-file raw_schema.json
	@echo "✅ Schema extracted to schema/raw_schema.json"

# Enrich schema with additional information
schema-enrich: env-setup
	@echo "Enriching schema with descriptions and metadata..."
	@if [ ! -f schema/raw_schema.json ]; then \
		echo "⚠️ Raw schema not found. Run 'make schema-extract' first."; \
		exit 1; \
	fi
	. .venv/bin/activate && . .env && python app/schema_enricher.py --schema schema/raw_schema.json --db example.sqlite --output schema/enriched_schema.json
	@echo "✅ Schema enriched and saved to schema/enriched_schema.json"

# Generate embeddings for schema elements
schema-embed: env-setup
	@echo "Generating embeddings for schema elements..."
	@if [ ! -f schema/enriched_schema.json ]; then \
		echo "⚠️ Enriched schema not found. Run 'make schema-enrich' first."; \
		exit 1; \
	fi
	. .venv/bin/activate && . .env && python app/schema_embedder.py --schema schema/enriched_schema.json --model local --output schema/schema_embeddings.pkl
	@echo "✅ Schema embeddings generated and saved to schema/schema_embeddings.pkl"

# Run full schema documentation workflow
schema-docs: env-setup
	@echo "Generating complete schema documentation..."
	@mkdir -p schema
	. .venv/bin/activate && . .env && python app/create_schema.py --db example.sqlite --output-dir schema
	@echo "✅ Complete schema documentation generated in schema directory"

# Generate pure database-only schema with enum/option values
schema-pure: env-setup
	@echo "Generating pure database schema with enum/option values..."
	@mkdir -p schema
	. .venv/bin/activate && . .env && python schema_generator.py --db example.sqlite --output-dir schema --output-file pure_schema.json
	@echo "✅ Pure schema extracted to schema/pure_schema.json" 