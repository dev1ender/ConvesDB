#!/usr/bin/env python3
"""
Script to seed Neo4j with high-dimensional, production-mimicking cybersecurity graph data.
"""

import os
import sys
import argparse
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.neo4j_connector import Neo4jConnector
from app.utils.logging_setup import setup_logging, get_logger

# Setup logger
setup_logging()
logger = get_logger(__name__)

fake = Faker()
Faker.seed(42)
random.seed(42)

# --- ENUMS & CONSTANTS ---
USER_ROLES = ["admin", "analyst", "user", "guest"]
USER_STATUS = ["active", "inactive", "locked"]
DEVICE_TYPES = ["laptop", "desktop", "mobile", "server", "iot"]
DEVICE_STATUS = ["online", "offline", "compromised"]
WEBSITE_CATEGORIES = ["social", "news", "shopping", "malware", "phishing", "work"]
WEBSITE_SSL = ["A", "B", "C", "D", "F"]
EMAIL_STATUS = ["active", "disabled", "compromised"]
MESSAGE_STATUS = ["delivered", "read", "quarantined", "failed"]
FILE_TYPES = ["pdf", "exe", "docx", "jpg", "zip"]
APP_STATUS = ["installed", "uninstalled", "outdated"]
NETWORK_TYPES = ["internal", "external", "dmz"]
NETWORK_STATUS = ["active", "inactive"]
EVENT_TYPES = ["login", "file_access", "malware_detected", "phishing_attempt", "data_exfiltration", "alert"]
EVENT_SEVERITY = ["low", "medium", "high", "critical"]
EVENT_STATUS = ["open", "closed", "in_progress"]
ALERT_TYPES = ["intrusion", "malware", "phishing", "policy_violation"]
ALERT_STATUS = ["new", "acknowledged", "resolved"]
ORG_INDUSTRY = ["finance", "healthcare", "education", "tech", "government"]
IP_TYPES = ["ipv4", "ipv6"]

# --- NODE GENERATORS ---
def gen_semver():
    return f"{random.randint(0, 5)}.{random.randint(0, 20)}.{random.randint(0, 50)}"

def gen_user(org_ids, location_ids):
    uid = str(uuid4())
    return {
        "label": "User",
        "properties": {
            "id": uid,
            "name": fake.name(),
            "email": fake.email(),
            "role": random.choice(USER_ROLES),
            "status": random.choice(USER_STATUS),
            "created_at": fake.date_time_this_decade().isoformat(),
            "last_login": fake.date_time_this_year().isoformat(),
            "timezone": fake.timezone(),
            "location_lat": float(fake.latitude()),
            "location_lon": float(fake.longitude()),
            "phone": fake.phone_number(),
            "department": fake.job(),
            "organization_id": random.choice(org_ids),
            "risk_score": round(random.uniform(0, 1), 2),
            "is_mfa_enabled": fake.boolean(),
            "avatar_url": fake.image_url(),
            "tags": fake.words(nb=3),
            "notes": fake.sentence()
        }
    }

def gen_device(user_ids, location_ids):
    did = str(uuid4())
    return {
        "label": "Device",
        "properties": {
            "id": did,
            "hostname": fake.hostname(),
            "ip_address": fake.ipv4_public(),
            "mac_address": fake.mac_address(),
            "os": fake.user_agent().split("/")[0],
            "device_type": random.choice(DEVICE_TYPES),
            "status": random.choice(DEVICE_STATUS),
            "last_seen": fake.date_time_this_year().isoformat(),
            "user_agent": fake.user_agent(),
            "location_lat": float(fake.latitude()),
            "location_lon": float(fake.longitude()),
            "serial_number": fake.uuid4(),
            "manufacturer": fake.company(),
            "model": fake.word(),
            "os_version": gen_semver(),
            "is_encrypted": fake.boolean(),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_website(org_ids):
    wid = str(uuid4())
    return {
        "label": "Website",
        "properties": {
            "id": wid,
            "url": fake.url(),
            "category": random.choice(WEBSITE_CATEGORIES),
            "risk_score": round(random.uniform(0, 1), 2),
            "last_scanned": fake.date_time_this_year().isoformat(),
            "is_blocked": fake.boolean(),
            "organization_id": random.choice(org_ids),
            "country": fake.country(),
            "registrar": fake.company(),
            "ssl_grade": random.choice(WEBSITE_SSL),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_email_account(user_ids):
    eid = str(uuid4())
    user_id = random.choice(user_ids)
    return {
        "label": "EmailAccount",
        "properties": {
            "id": eid,
            "email": fake.email(),
            "user_id": user_id,
            "provider": fake.free_email_domain(),
            "status": random.choice(EMAIL_STATUS),
            "created_at": fake.date_time_this_decade().isoformat(),
            "last_accessed": fake.date_time_this_year().isoformat(),
            "is_2fa_enabled": fake.boolean(),
            "recovery_email": fake.email(),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_message(email_ids):
    mid = str(uuid4())
    from_email = random.choice(email_ids)
    to_email = random.choice(email_ids)
    return {
        "label": "Message",
        "properties": {
            "id": mid,
            "from_email": from_email,
            "to_email": to_email,
            "subject": fake.sentence(nb_words=6),
            "body": fake.text(max_nb_chars=200),
            "sent_at": fake.date_time_this_year().isoformat(),
            "status": random.choice(MESSAGE_STATUS),
            "is_spam": fake.boolean(),
            "attachments": [fake.file_name() for _ in range(random.randint(0, 3))],
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_file(user_ids, device_ids):
    fid = str(uuid4())
    return {
        "label": "File",
        "properties": {
            "id": fid,
            "name": fake.file_name(),
            "path": fake.file_path(),
            "size": random.randint(100, 10000000),
            "hash": fake.sha256(),
            "file_type": random.choice(FILE_TYPES),
            "uploaded_by": random.choice(user_ids),
            "uploaded_at": fake.date_time_this_year().isoformat(),
            "is_malicious": fake.boolean(),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_application(device_ids):
    aid = str(uuid4())
    return {
        "label": "Application",
        "properties": {
            "id": aid,
            "name": fake.word(),
            "version": gen_semver(),
            "vendor": fake.company(),
            "install_date": fake.date_time_this_year().isoformat(),
            "last_used": fake.date_time_this_year().isoformat(),
            "status": random.choice(APP_STATUS),
            "device_id": random.choice(device_ids),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_network(org_ids):
    nid = str(uuid4())
    return {
        "label": "Network",
        "properties": {
            "id": nid,
            "name": fake.word() + "-net",
            "cidr": fake.ipv4_network_class(),
            "type": random.choice(NETWORK_TYPES),
            "status": random.choice(NETWORK_STATUS),
            "organization_id": random.choice(org_ids),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_location():
    lid = str(uuid4())
    return {
        "label": "Location",
        "properties": {
            "id": lid,
            "name": fake.city(),
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
            "country": fake.country(),
            "city": fake.city(),
            "timezone": fake.timezone(),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_event(user_ids, device_ids, website_ids, message_ids):
    eid = str(uuid4())
    event_type = random.choice(EVENT_TYPES)
    source_id = random.choice(user_ids + device_ids + website_ids + message_ids)
    target_id = random.choice(user_ids + device_ids + website_ids + message_ids)
    return {
        "label": "Event",
        "properties": {
            "id": eid,
            "event_type": event_type,
            "timestamp": fake.date_time_this_year().isoformat(),
            "source_id": source_id,
            "target_id": target_id,
            "severity": random.choice(EVENT_SEVERITY),
            "status": random.choice(EVENT_STATUS),
            "description": fake.sentence(),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_alert(event_ids):
    aid = str(uuid4())
    return {
        "label": "Alert",
        "properties": {
            "id": aid,
            "alert_type": random.choice(ALERT_TYPES),
            "created_at": fake.date_time_this_year().isoformat(),
            "status": random.choice(ALERT_STATUS),
            "severity": random.choice(EVENT_SEVERITY),
            "event_id": random.choice(event_ids),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_organization():
    oid = str(uuid4())
    return {
        "label": "Organization",
        "properties": {
            "id": oid,
            "name": fake.company(),
            "industry": random.choice(ORG_INDUSTRY),
            "country": fake.country(),
            "created_at": fake.date_time_this_decade().isoformat(),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

def gen_ipaddress():
    iid = str(uuid4())
    ip_type = random.choice(IP_TYPES)
    address = fake.ipv4_public() if ip_type == "ipv4" else fake.ipv6()
    return {
        "label": "IPAddress",
        "properties": {
            "id": iid,
            "address": address,
            "type": ip_type,
            "is_blacklisted": fake.boolean(),
            "country": fake.country(),
            "tags": fake.words(nb=2),
            "notes": fake.sentence()
        }
    }

# --- RELATIONSHIP GENERATORS ---
def gen_relationship(start, end, rel_type, extra_props=None):
    rel = {
        "start": start,
        "end": end,
        "type": rel_type,
        "properties": {
            "id": str(uuid4()),
            "timestamp": fake.date_time_this_year().isoformat(),
            "status": random.choice(["success", "failure", "pending"]),
            "tags": fake.words(nb=2),
            "details": fake.sentence()
        }
    }
    if extra_props:
        rel["properties"].update(extra_props)
    return rel

# --- DATA GENERATION ---
def generate_data(num_nodes=1000):
    logger.info(f"Generating {num_nodes} nodes and relationships...")
    # Distribute nodes across types
    orgs = [gen_organization() for _ in range(10)]
    org_ids = [o["properties"]["id"] for o in orgs]
    locations = [gen_location() for _ in range(20)]
    location_ids = [l["properties"]["id"] for l in locations]
    users = [gen_user(org_ids, location_ids) for _ in range(150)]
    user_ids = [u["properties"]["id"] for u in users]
    devices = [gen_device(user_ids, location_ids) for _ in range(150)]
    device_ids = [d["properties"]["id"] for d in devices]
    websites = [gen_website(org_ids) for _ in range(100)]
    website_ids = [w["properties"]["id"] for w in websites]
    email_accounts = [gen_email_account(user_ids) for _ in range(120)]
    email_ids = [e["properties"]["id"] for e in email_accounts]
    messages = [gen_message(email_ids) for _ in range(200)]
    message_ids = [m["properties"]["id"] for m in messages]
    files = [gen_file(user_ids, device_ids) for _ in range(100)]
    file_ids = [f["properties"]["id"] for f in files]
    applications = [gen_application(device_ids) for _ in range(100)]
    app_ids = [a["properties"]["id"] for a in applications]
    networks = [gen_network(org_ids) for _ in range(40)]
    network_ids = [n["properties"]["id"] for n in networks]
    events = [gen_event(user_ids, device_ids, website_ids, message_ids) for _ in range(80)]
    event_ids = [e["properties"]["id"] for e in events]
    alerts = [gen_alert(event_ids) for _ in range(50)]
    alert_ids = [a["properties"]["id"] for a in alerts]
    ipaddresses = [gen_ipaddress() for _ in range(50)]
    ip_ids = [ip["properties"]["id"] for ip in ipaddresses]

    nodes = orgs + locations + users + devices + websites + email_accounts + messages + files + applications + networks + events + alerts + ipaddresses

    # --- Relationship mapping for plausible connections ---
    node_type_map = {
        "User": users,
        "Device": devices,
        "Website": websites,
        "EmailAccount": email_accounts,
        "Message": messages,
        "File": files,
        "Application": applications,
        "Network": networks,
        "Location": locations,
        "Event": events,
        "Alert": alerts,
        "Organization": orgs,
        "IPAddress": ipaddresses
    }
    # For each node type, define possible outgoing relationships and valid target types
    rel_schema = {
        "User": [
            ("LOGGED_IN_FROM", "Device"),
            ("ACCESSED", "Website"),
            ("SENT", "Message"),
            ("OWNS", "Device"),
            ("WORKS_FOR", "Organization"),
            ("UPLOADED_BY", "File"),
            ("BELONGS_TO", "EmailAccount")
        ],
        "Device": [
            ("CONNECTED_TO", "Network"),
            ("LOCATED_AT", "Location"),
            ("HAS_IP", "IPAddress"),
            ("INSTALLED", "Application"),
            ("STORED_ON", "File"),
            ("HOSTED_ON", "Website")
        ],
        "Website": [
            ("REGISTERED_TO", "Organization"),
            ("HOSTED_ON", "Device"),
            ("ACCESSED_BY", "User")
        ],
        "EmailAccount": [
            ("BELONGS_TO", "User"),
            ("SENT_FROM", "Message"),
            ("SENT_TO", "Message")
        ],
        "Message": [
            ("SENT_FROM", "EmailAccount"),
            ("SENT_TO", "EmailAccount")
        ],
        "File": [
            ("UPLOADED_BY", "User"),
            ("STORED_ON", "Device")
        ],
        "Application": [
            ("INSTALLED_ON", "Device")
        ],
        "Network": [
            ("HAS_DEVICE", "Device"),
            ("BELONGS_TO", "Organization")
        ],
        "Location": [
            ("HAS_DEVICE", "Device"),
            ("HAS_USER", "User")
        ],
        "Event": [
            ("TRIGGERED_BY", "User"),
            ("TRIGGERED_BY", "Device"),
            ("TRIGGERED_BY", "Website"),
            ("NEXT_EVENT", "Event")
        ],
        "Alert": [
            ("RELATED_TO", "Event")
        ],
        "Organization": [
            ("HAS_NETWORK", "Network"),
            ("HAS_USER", "User")
        ],
        "IPAddress": [
            ("ASSIGNED_TO", "Device"),
            ("ASSIGNED_TO", "Website"),
            ("ASSIGNED_TO", "Organization")
        ]
    }

    # --- Generate relationships ---
    relationships = []
    rel_set = set()  # To avoid duplicates
    # For each node, randomly create a number of outgoing relationships
    for node in nodes:
        label = node["label"]
        node_id = node["properties"]["id"]
        if label not in rel_schema:
            continue
        # Use a Poisson distribution for number of outgoing edges (mean=3, min=1, max=8)
        num_rels = min(max(1, int(random.gauss(3, 2))), 8)
        for _ in range(num_rels):
            rel_type, target_type = random.choice(rel_schema[label])
            # Avoid self-loops unless allowed (e.g., Event->NEXT_EVENT)
            possible_targets = node_type_map[target_type]
            if not possible_targets:
                continue
            target = random.choice(possible_targets)
            target_id = target["properties"]["id"]
            if label == target_type and node_id == target_id and rel_type != "NEXT_EVENT":
                continue  # skip self-loop unless it's NEXT_EVENT
            # Avoid duplicate relationships
            rel_key = (label, node_id, rel_type, target_type, target_id)
            if rel_key in rel_set:
                continue
            rel_set.add(rel_key)
            relationships.append(gen_relationship(
                {"label": label, "property": "id", "value": node_id},
                {"label": target_type, "property": "id", "value": target_id},
                rel_type
            ))
    logger.info(f"Generated {len(nodes)} nodes and {len(relationships)} relationships.")
    return nodes, relationships

# --- NEO4J SEEDING ---
def seed_neo4j(config: Dict[str, Any], num_nodes=1000) -> None:
    logger.info("Seeding Neo4j database with high-dimensional test data")
    connector = None
    try:
        connector = Neo4jConnector(config)
        connector.connect()
        if config.get("clear_existing", True):
            logger.info("Clearing existing data")
            connector.run("MATCH (n) DETACH DELETE n")
        nodes, relationships = generate_data(num_nodes)
        # Insert nodes
        for node in nodes:
            label = node["label"]
            properties = node["properties"]
            props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
            query = f"CREATE (:{label} {{{props_str}}})"
            connector.run(query, properties)
        logger.info(f"Created {len(nodes)} nodes")
        # Insert relationships
        for rel in relationships:
            start = rel["start"]
            end = rel["end"]
            rel_type = rel["type"]
            properties = rel["properties"]
            start_label = start["label"]
            start_prop = start["property"]
            start_value = start["value"]
            end_label = end["label"]
            end_prop = end["property"]
            end_value = end["value"]
            query = f"""
            MATCH (a:{start_label}), (b:{end_label})
            WHERE a.{start_prop} = $start_value AND b.{end_prop} = $end_value
            CREATE (a)-[r:{rel_type} {{{', '.join([f'{k}: ${k}' for k in properties.keys()])}}}]->(b)
            """
            params = {"start_value": start_value, "end_value": end_value}
            params.update(properties)
            connector.run(query, params)
        logger.info(f"Created {len(relationships)} relationships")
        # Create indexes for key properties
        logger.info("Creating indexes")
        for label in ["User", "Device", "Website", "EmailAccount", "Message", "File", "Application", "Network", "Location", "Event", "Alert", "Organization", "IPAddress"]:
            connector.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.id)")
        logger.info("Neo4j database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding Neo4j database: {str(e)}")
        raise
    finally:
        if connector:
            connector.close()

def main():
    parser = argparse.ArgumentParser(description='Seed Neo4j database with high-dimensional test data')
    parser.add_argument('--uri', type=str, default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--username', type=str, default='neo4j', help='Neo4j username')
    parser.add_argument('--password', type=str, default='password', help='Neo4j password')
    parser.add_argument('--database', type=str, default='neo4j', help='Neo4j database name')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
    parser.add_argument('--num-nodes', type=int, default=1000, help='Approximate number of nodes to generate')
    args = parser.parse_args()
    config = {
        "uri": args.uri,
        "username": args.username,
        "password": args.password,
        "database": args.database,
        "clear_existing": args.clear
    }
    seed_neo4j(config, num_nodes=args.num_nodes)

# --- Example NLP Questions and Cypher Queries for Testing ---
SAMPLE_NEO4J_QUERIES = [
    {
        "complexity": "low",
        "nlp": "How many users are in the database?",
        "cypher": "MATCH (u:User) RETURN count(u) AS user_count",
        "expected": "~150"
    },
    {
        "complexity": "low",
        "nlp": "List all device hostnames.",
        "cypher": "MATCH (d:Device) RETURN d.hostname",
        "expected": "150 rows"
    },
    {
        "complexity": "low",
        "nlp": "How many organizations are there?",
        "cypher": "MATCH (o:Organization) RETURN count(o) AS org_count",
        "expected": "10"
    },
    {
        "complexity": "medium",
        "nlp": "Which users have uploaded files?",
        "cypher": "MATCH (u:User)-[:UPLOADED_BY]->(f:File) RETURN DISTINCT u.name",
        "expected": "Dozens (depends on random connections)"
    },
    {
        "complexity": "medium",
        "nlp": "How many devices are currently online?",
        "cypher": "MATCH (d:Device) WHERE d.status = 'online' RETURN count(d) AS online_devices",
        "expected": "~30-50 (random, but a subset of 150)"
    },
    {
        "complexity": "medium",
        "nlp": "List all websites accessed by users from the IT department.",
        "cypher": "MATCH (u:User)-[:ACCESSED]->(w:Website) WHERE u.department CONTAINS 'IT' RETURN DISTINCT w.url",
        "expected": "A handful to dozens, depending on random data"
    },
    {
        "complexity": "medium",
        "nlp": "Which organizations have at least one network?",
        "cypher": "MATCH (o:Organization)-[:HAS_NETWORK]->(n:Network) RETURN DISTINCT o.name",
        "expected": "Most organizations (10), since each is likely to have at least one network"
    },
    {
        "complexity": "advanced",
        "nlp": "Find users who have logged in from a device that is currently marked as compromised.",
        "cypher": "MATCH (u:User)-[:LOGGED_IN_FROM]->(d:Device) WHERE d.status = 'compromised' RETURN DISTINCT u.name, d.hostname",
        "expected": "Several, depending on random assignment"
    },
    {
        "complexity": "advanced",
        "nlp": "Which users have triggered a high or critical severity event in the last year?",
        "cypher": "MATCH (e:Event)-[:TRIGGERED_BY]->(u:User) WHERE e.severity IN ['high', 'critical'] AND datetime(e.timestamp) > datetime() - duration({years:1}) RETURN DISTINCT u.name, e.event_type, e.severity, e.timestamp",
        "expected": "A handful, depending on event generation"
    },
    {
        "complexity": "advanced",
        "nlp": "List all devices that have both a file stored on them and are assigned an IP address from a blacklisted country.",
        "cypher": "MATCH (d:Device)-[:STORED_ON]->(f:File) MATCH (d)-[:HAS_IP]->(ip:IPAddress) WHERE ip.is_blacklisted = true RETURN DISTINCT d.hostname, ip.address, f.name",
        "expected": "A few, depending on random data"
    }
]

if __name__ == '__main__':
    main() 