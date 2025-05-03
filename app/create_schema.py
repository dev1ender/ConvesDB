#!/usr/bin/env python3

"""
Schema Documentation Workflow

This script combines all schema documentation steps into one workflow:
1. Extract schema from database
2. Enrich schema with additional information
3. Generate embeddings for semantic search

It creates a complete set of schema artifacts for LLM reasoning.
"""

import os
import argparse
import json
import shutil
from pathlib import Path
import sys
from datetime import datetime

# Ensure the app directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the three main components
from app.schema_extractor import SchemaExtractor
from app.schema_enricher import SchemaEnricher
from app.schema_embedder import SchemaEmbedder


def setup_output_directory(base_dir: str, overwrite: bool = False) -> str:
    """Set up the output directory with timestamp."""
    # Create a timestamped directory name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, f"schema_{timestamp}")
    
    # Check if directory exists
    if os.path.exists(output_dir):
        if overwrite:
            shutil.rmtree(output_dir)
        else:
            print(f"Output directory already exists: {output_dir}")
            print("Use --overwrite to replace existing directory or choose a different base directory")
            sys.exit(1)
    
    # Create the directory
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def extract_schema(db_path: str, output_dir: str) -> str:
    """Extract schema from database."""
    print("\n=== STEP 1: Extracting Schema ===")
    
    extractor = SchemaExtractor(db_path, output_dir)
    schema = extractor.extract_schema()
    output_path = extractor.save_schema("raw_schema.json")
    
    print(f"Raw schema extracted with {schema['metadata']['tables_count']} tables and "
          f"{schema['metadata']['views_count']} views")
    return output_path


def enrich_schema(schema_path: str, db_path: str, output_dir: str) -> str:
    """Enrich schema with additional information."""
    print("\n=== STEP 2: Enriching Schema ===")
    
    enricher = SchemaEnricher(schema_path, db_path)
    enricher.analyze_and_enrich()
    output_path = os.path.join(output_dir, "enriched_schema.json")
    enricher.save_schema(output_path)
    enricher.close()
    
    print(f"Schema enriched with descriptions, semantic types, and hints")
    return output_path


def generate_embeddings(schema_path: str, model: str, openai_key: str, output_dir: str) -> tuple:
    """Generate embeddings for schema elements."""
    print("\n=== STEP 3: Generating Embeddings ===")
    
    embedder = SchemaEmbedder(schema_path, model, openai_key)
    embedder.generate_embeddings()
    
    # Save embeddings
    embeddings_path = os.path.join(output_dir, "schema_embeddings.pkl")
    metadata_path = os.path.join(output_dir, "embedding_metadata.json")
    
    embedder.save_embeddings(embeddings_path)
    embedder.save_embedding_metadata(metadata_path)
    
    print(f"Embeddings generated using {model} model")
    return embeddings_path, metadata_path


def generate_readme(output_dir: str, db_path: str, stats: dict) -> str:
    """Generate a README with summary information."""
    readme_path = os.path.join(output_dir, "README.md")
    
    with open(readme_path, 'w') as f:
        f.write(f"# Schema Documentation for {os.path.basename(db_path)}\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Tables: {stats['tables']}\n")
        f.write(f"- Views: {stats['views']}\n")
        f.write(f"- Relationships: {stats['relationships']}\n")
        f.write(f"- Indexes: {stats['indexes']}\n")
        f.write(f"- Embedded elements: {stats['embedded_elements']}\n\n")
        
        f.write("## Files\n\n")
        f.write("- `raw_schema.json`: Raw schema extracted from the database\n")
        f.write("- `enriched_schema.json`: Schema enriched with descriptions and hints\n")
        f.write("- `schema_embeddings.pkl`: Vector embeddings for schema elements\n")
        f.write("- `embedding_metadata.json`: Metadata about the embeddings (without vectors)\n\n")
        
        f.write("## Usage with LLMs\n\n")
        f.write("You can use these files in several ways:\n\n")
        f.write("1. Direct embedding of schema JSON in prompts\n")
        f.write("2. RAG approach using the embeddings for semantic search\n")
        f.write("3. Building targeted context using the schema information\n")
        f.write("4. Schema agent implementation\n\n")
        
        f.write("See the main README for more details.\n")
    
    print(f"README generated at {readme_path}")
    return readme_path


def main():
    parser = argparse.ArgumentParser(description="Generate complete schema documentation for LLM reasoning")
    parser.add_argument("--db", help="Path to SQLite database file", required=True)
    parser.add_argument("--output-dir", help="Base directory for output files", default="schema")
    parser.add_argument("--model", help="Embedding model (local or openai)", default="local")
    parser.add_argument("--openai-key", help="OpenAI API key (if using OpenAI model)")
    parser.add_argument("--overwrite", help="Overwrite existing output directory", action="store_true")
    args = parser.parse_args()
    
    # Set up output directory
    output_dir = setup_output_directory(args.output_dir, args.overwrite)
    print(f"Output will be saved to: {output_dir}")
    
    # Extract schema
    schema_path = extract_schema(args.db, output_dir)
    
    # Enrich schema
    enriched_path = enrich_schema(schema_path, args.db, output_dir)
    
    # Generate embeddings
    embeddings_path, metadata_path = generate_embeddings(
        enriched_path, args.model, args.openai_key, output_dir
    )
    
    # Load some stats for the README
    with open(enriched_path, 'r') as f:
        schema = json.load(f)
    
    with open(metadata_path, 'r') as f:
        embedding_metadata = json.load(f)
    
    stats = {
        "tables": schema['metadata']['tables_count'],
        "views": schema['metadata']['views_count'],
        "relationships": schema['metadata']['relationships_count'],
        "indexes": schema['metadata']['index_count'],
        "embedded_elements": embedding_metadata['element_count']
    }
    
    # Generate README
    readme_path = generate_readme(output_dir, args.db, stats)
    
    print("\n=== Schema Documentation Complete ===")
    print(f"All output is available in: {output_dir}")
    print("Files generated:")
    for file in os.listdir(output_dir):
        print(f"- {file}")


if __name__ == "__main__":
    main() 