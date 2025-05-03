#!/usr/bin/env python3
"""
Script to seed Neo4j with large-scale realistic data for RAG system.
This script generates a much larger academic knowledge graph with synthetic data.
"""

import os
import sys
import argparse
import random
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.neo4j_connector import Neo4jConnector
from app.utils.logging_setup import setup_logging, get_logger

# Setup logger
setup_logging()
logger = get_logger(__name__)

# Constants for data generation
PAPER_COUNT = 1000
AUTHOR_COUNT = 300
ORGANIZATION_COUNT = 50
CONFERENCE_COUNT = 20
TOPIC_COUNT = 100
YEARS = range(2010, 2024)
COUNTRIES = ["USA", "UK", "Germany", "France", "Japan", "China", "Canada", "Australia", "India", "Brazil"]
ORG_TYPES = ["University", "Industry", "Research Institute", "Government"]
PAPER_TITLE_PREFIXES = [
    "Advances in", "Novel", "Improved", "Efficient", "Exploring", 
    "Understanding", "Learning", "Optimizing", "Deep", "Neural",
    "Transformative", "Scaling", "Robust", "Adaptive", "Integrating"
]
PAPER_TITLE_TOPICS = [
    "Neural Networks", "Machine Learning", "Natural Language Processing",
    "Computer Vision", "Reinforcement Learning", "Knowledge Graphs",
    "Information Retrieval", "Graph Neural Networks", "Transformers",
    "Recommendation Systems", "Time Series Analysis", "Adversarial Learning",
    "Federated Learning", "Transfer Learning", "Data Mining"
]
PAPER_TITLE_SUFFIXES = [
    "for Large-scale Applications", "using Deep Learning", "with Graph Neural Networks",
    "in Real-world Settings", "for Low-resource Scenarios", "with Transfer Learning",
    "through Knowledge Graphs", "via Self-supervision", "with Attention Mechanisms",
    "for Multimodal Data", "with Language Models", "for Production Systems"
]
CONFERENCE_NAMES = [
    "ACL", "NeurIPS", "ICML", "ICLR", "SIGIR", "WWW", "KDD", "AAAI",
    "IJCAI", "CVPR", "ICCV", "ECCV", "EMNLP", "NAACL", "COLING",
    "RecSys", "WSDM", "CIKM", "SIGMOD", "VLDB"
]
TOPIC_PREFIXES = [
    "Large Language Models", "Graph Neural Networks", "Knowledge Graphs",
    "Information Retrieval", "Natural Language Processing", "Reinforcement Learning",
    "Computer Vision", "Machine Learning", "Deep Learning", "Data Mining",
    "Neural Networks", "Attention Mechanisms", "Transformers", "Generative Models"
]
TOPIC_APPLICATIONS = [
    "for Healthcare", "in Finance", "for Recommendation", "in Education",
    "for Scientific Discovery", "in Social Media", "for Search Engines",
    "in Autonomous Systems", "for Content Generation", "in Robotics"
]
LOCATIONS = [
    "New York", "San Francisco", "London", "Paris", "Berlin", "Tokyo",
    "Sydney", "Singapore", "Toronto", "Beijing", "Seoul", "Amsterdam",
    "Barcelona", "Vienna", "Zurich", "Seattle", "Boston", "Chicago",
    "Montreal", "Vancouver", "Hong Kong", "Dublin", "Stockholm", "Helsinki"
]

def generate_realistic_data() -> Dict[str, Any]:
    """Generate realistic large-scale academic knowledge graph data.
    
    Returns:
        Dictionary with nodes and relationships
    """
    logger.info("Generating large-scale realistic data...")
    
    # Track start time for performance monitoring
    start_time = time.time()
    
    # Initialize data structure
    data = {
        "nodes": [],
        "relationships": []
    }
    
    # Generate organizations
    logger.info(f"Generating {ORGANIZATION_COUNT} organizations...")
    organizations = []
    for i in range(ORGANIZATION_COUNT):
        org_type = random.choice(ORG_TYPES)
        suffix = "University" if org_type == "University" else random.choice(["Research", "Labs", "Institute", "Technologies"])
        
        # Generate organization name
        if org_type == "University":
            prefix = random.choice(["North", "South", "East", "West", "Central", "Pacific", "Atlantic", "National", "International", "Global"])
            city = random.choice(LOCATIONS)
            name = f"{prefix} {city} {suffix}"
        else:
            names = ["Tech", "Advanced", "Global", "Future", "Quantum", "Nexus", "Vertex", "Alpha", "Omega", "Nova"]
            name = f"{random.choice(names)} {suffix}"
        
        # Add organization
        org = {
            "label": "Organization",
            "properties": {
                "id": f"org_{i}",
                "name": name,
                "country": random.choice(COUNTRIES),
                "type": org_type,
                "founded": random.randint(1900, 2020)
            }
        }
        organizations.append(org)
        data["nodes"].append(org)
    
    # Generate authors
    logger.info(f"Generating {AUTHOR_COUNT} authors...")
    authors = []
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
                   "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
                   "Wei", "Liu", "Zhang", "Chen", "Li", "Amir", "Mohammed", "Fatima", "Juan", "Carlos",
                   "Marie", "Sophie", "Hans", "Ava", "Noah", "Emma", "Oliver", "Charlotte", "Elijah", "Amelia"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
                  "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson",
                  "Wang", "Li", "Zhang", "Chen", "Liu", "Singh", "Patel", "Kim", "Nguyen", "Müller",
                  "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", "Schäfer"]
    
    for i in range(AUTHOR_COUNT):
        # Assign random organization
        org = random.choice(organizations)
        
        # Generate author
        author = {
            "label": "Author",
            "properties": {
                "id": f"author_{i}",
                "name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "affiliation": org["properties"]["name"],
                "h_index": random.randint(0, 50),
                "papers_count": random.randint(1, 100)
            }
        }
        authors.append(author)
        data["nodes"].append(author)
        
        # Create affiliation relationship
        data["relationships"].append({
            "start": {"label": "Author", "property": "id", "value": author["properties"]["id"]},
            "end": {"label": "Organization", "property": "id", "value": org["properties"]["id"]},
            "type": "AFFILIATED_WITH"
        })
    
    # Generate topics
    logger.info(f"Generating {TOPIC_COUNT} topics...")
    topics = []
    for i in range(TOPIC_COUNT):
        if random.random() < 0.7:  # 70% chance for application topics
            topic_name = f"{random.choice(TOPIC_PREFIXES)} {random.choice(TOPIC_APPLICATIONS)}"
        else:
            topic_name = random.choice(TOPIC_PREFIXES)
        
        topic = {
            "label": "Topic",
            "properties": {
                "id": f"topic_{i}",
                "name": topic_name,
                "popularity": random.uniform(0.1, 1.0)
            }
        }
        topics.append(topic)
        data["nodes"].append(topic)
    
    # Create topic relationships (build topic hierarchy)
    logger.info("Creating topic relationships...")
    for i in range(TOPIC_COUNT):
        # Each topic has a 70% chance to be related to 1-3 other topics
        if random.random() < 0.7:
            related_count = random.randint(1, 3)
            for _ in range(related_count):
                related_topic = random.choice(topics)
                if related_topic != topics[i]:  # Avoid self-relations
                    data["relationships"].append({
                        "start": {"label": "Topic", "property": "id", "value": topics[i]["properties"]["id"]},
                        "end": {"label": "Topic", "property": "id", "value": related_topic["properties"]["id"]},
                        "type": "RELATED_TO"
                    })
    
    # Generate conferences
    logger.info(f"Generating {CONFERENCE_COUNT} conferences...")
    conferences = []
    for i in range(CONFERENCE_COUNT):
        conf_name = CONFERENCE_NAMES[i] if i < len(CONFERENCE_NAMES) else f"Conf{i}"
        
        # Generate multiple years of the same conference
        for year in random.sample(list(YEARS), random.randint(1, len(YEARS))):
            conference = {
                "label": "Conference",
                "properties": {
                    "id": f"conf_{conf_name}_{year}",
                    "name": conf_name,
                    "year": year,
                    "location": random.choice(LOCATIONS),
                    "attendees": random.randint(500, 5000)
                }
            }
            conferences.append(conference)
            data["nodes"].append(conference)
    
    # Generate papers
    logger.info(f"Generating {PAPER_COUNT} papers...")
    papers = []
    for i in range(PAPER_COUNT):
        # Generate paper title
        title = f"{random.choice(PAPER_TITLE_PREFIXES)} {random.choice(PAPER_TITLE_TOPICS)} {random.choice(PAPER_TITLE_SUFFIXES)}"
        
        # Assign paper to a random year
        year = random.choice(YEARS)
        
        # Create paper node
        paper = {
            "label": "Paper",
            "properties": {
                "id": f"paper_{i}",
                "title": title,
                "year": year,
                "doi": f"10.{random.randint(1000, 9999)}/{random.randint(10000, 99999)}",
                "citations": random.randint(0, 1000)
            }
        }
        papers.append(paper)
        data["nodes"].append(paper)
        
        # Assign 1-5 authors to the paper
        paper_authors = random.sample(authors, random.randint(1, min(5, len(authors))))
        for author in paper_authors:
            data["relationships"].append({
                "start": {"label": "Paper", "property": "id", "value": paper["properties"]["id"]},
                "end": {"label": "Author", "property": "id", "value": author["properties"]["id"]},
                "type": "AUTHORED_BY"
            })
        
        # Assign 1-3 topics to the paper
        paper_topics = random.sample(topics, random.randint(1, min(3, len(topics))))
        for topic in paper_topics:
            data["relationships"].append({
                "start": {"label": "Paper", "property": "id", "value": paper["properties"]["id"]},
                "end": {"label": "Topic", "property": "id", "value": topic["properties"]["id"]},
                "type": "HAS_TOPIC"
            })
        
        # Assign paper to a conference from the matching year
        matching_conferences = [conf for conf in conferences if conf["properties"]["year"] == year]
        if matching_conferences:
            conference = random.choice(matching_conferences)
            data["relationships"].append({
                "start": {"label": "Paper", "property": "id", "value": paper["properties"]["id"]},
                "end": {"label": "Conference", "property": "id", "value": conference["properties"]["id"]},
                "type": "PUBLISHED_AT"
            })
    
    # Generate citations between papers (papers can only cite older papers)
    logger.info("Generating paper citations...")
    sorted_papers = sorted(papers, key=lambda p: p["properties"]["year"])
    for i, paper in enumerate(sorted_papers):
        # Each paper has a chance to cite 0-20 earlier papers
        if i > 0:  # Must be at least one earlier paper
            citation_count = min(i, random.randint(0, 20))
            if citation_count > 0:
                cited_papers = random.sample(sorted_papers[:i], citation_count)
                for cited_paper in cited_papers:
                    data["relationships"].append({
                        "start": {"label": "Paper", "property": "id", "value": paper["properties"]["id"]},
                        "end": {"label": "Paper", "property": "id", "value": cited_paper["properties"]["id"]},
                        "type": "CITES"
                    })
    
    # Log statistics
    logger.info(f"Generated {len(data['nodes'])} nodes and {len(data['relationships'])} relationships")
    logger.info(f"Data generation took {time.time() - start_time:.2f} seconds")
    
    return data

def seed_neo4j_large(config: Dict[str, Any]) -> None:
    """Seed Neo4j database with large-scale realistic data.
    
    Args:
        config: Neo4j configuration dictionary
    """
    logger.info("Seeding Neo4j database with large-scale realistic data")
    
    try:
        # Connect to Neo4j
        connector = Neo4jConnector(config)
        connector.connect()
        
        # Clear existing data if requested
        if config.get("clear_existing", True):
            logger.info("Clearing existing data")
            connector.run("MATCH (n) DETACH DELETE n")
        
        # Generate data
        data = generate_realistic_data()
        
        # Create nodes in batches
        batch_size = 100
        logger.info(f"Creating nodes in batches of {batch_size}...")
        
        for i in range(0, len(data["nodes"]), batch_size):
            batch = data["nodes"][i:i+batch_size]
            
            # Build Cypher query for batch node creation
            query = """
            UNWIND $nodes AS node
            CALL apoc.create.node([node.label], node.properties) YIELD node AS n
            RETURN count(n)
            """
            
            # Execute query
            connector.run(query, {"nodes": batch})
            logger.info(f"Created nodes {i+1} to {min(i+batch_size, len(data['nodes']))}")
        
        # Create indexes for better performance
        logger.info("Creating indexes")
        connector.run("CREATE INDEX IF NOT EXISTS FOR (p:Paper) ON (p.id)")
        connector.run("CREATE INDEX IF NOT EXISTS FOR (a:Author) ON (a.id)")
        connector.run("CREATE INDEX IF NOT EXISTS FOR (o:Organization) ON (o.id)")
        connector.run("CREATE INDEX IF NOT EXISTS FOR (t:Topic) ON (t.id)")
        connector.run("CREATE INDEX IF NOT EXISTS FOR (c:Conference) ON (c.id)")
        
        # Create relationships in batches
        logger.info(f"Creating relationships in batches of {batch_size}...")
        
        for i in range(0, len(data["relationships"]), batch_size):
            batch = data["relationships"][i:i+batch_size]
            
            # Build Cypher query for batch relationship creation
            query = """
            UNWIND $rels AS rel
            MATCH (a {id: rel.start.value})
            MATCH (b {id: rel.end.value})
            CALL apoc.create.relationship(a, rel.type, {}, b) YIELD rel AS r
            RETURN count(r)
            """
            
            # Execute query
            connector.run(query, {"rels": batch})
            logger.info(f"Created relationships {i+1} to {min(i+batch_size, len(data['relationships']))}")
        
        logger.info("Neo4j database seeded successfully with large-scale data")
        
    except Exception as e:
        logger.error(f"Error seeding Neo4j database: {str(e)}")
        raise
    finally:
        if connector:
            connector.close()

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Seed Neo4j database with large-scale realistic data')
    
    parser.add_argument('--uri', type=str, default='bolt://localhost:7687',
                       help='Neo4j URI')
    parser.add_argument('--username', type=str, default='neo4j',
                       help='Neo4j username')
    parser.add_argument('--password', type=str, default='password',
                       help='Neo4j password')
    parser.add_argument('--database', type=str, default='neo4j',
                       help='Neo4j database name')
    parser.add_argument('--clear', action='store_true',
                       help='Clear existing data before seeding')
    
    args = parser.parse_args()
    
    # Prepare configuration
    config = {
        "uri": args.uri,
        "username": args.username,
        "password": args.password,
        "database": args.database,
        "clear_existing": args.clear
    }
    
    # Seed database
    seed_neo4j_large(config)

if __name__ == '__main__':
    main() 