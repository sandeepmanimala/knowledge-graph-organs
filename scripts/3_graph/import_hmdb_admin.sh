#!/bin/bash
# -----------------------------------------------------------------------------
# Script: import_hmdb_admin.sh
# Purpose: Uses the highly optimized `neo4j-admin database import` tool to load
#          the millions of Metabolomics nodes and edges directly into the database.
#
# WARNING: The Neo4j database service MUST BE STOPPED before running this command.
# -----------------------------------------------------------------------------

set -e # Exit immediately if a command fails

# Variables
DB_NAME="neo4j"
IMPORT_DIR="/var/lib/neo4j/import/hmdb" # Path inside the neo4j docker container or server
NEO4J_HOME="/var/lib/neo4j" # Assuming standard linux installation

echo "🛑 Stopping Neo4j Service..."
sudo systemctl stop neo4j || echo "Warning: Could not stop neo4j via systemctl. If running Docker, use 'docker stop <container>'."

echo "🧹 Clearing existing database to allow fresh import (if starting from scratch)..."
# Warning: This deletes the database files to allow admin import. If you want to MERGE
# data into an existing database, you cannot use admin import. You must use 'apoc.periodic.iterate'
# or the cypher LOAD CSV. However, admin import is the only way to load billions of rows initially.
# sudo rm -rf ${NEO4J_HOME}/data/databases/${DB_NAME}
# sudo rm -rf ${NEO4J_HOME}/data/transactions/${DB_NAME}

echo "🚀 Starting High-Speed Neo4j Admin Import..."

sudo -u neo4j neo4j-admin database import full ${DB_NAME} \
    --nodes=Metabolite="${IMPORT_DIR}/metabolites_nodes.csv" \
    --relationships=ASSOCIATED_WITH_DISEASE="${IMPORT_DIR}/metabolites_to_diseases.csv" \
    --relationships=BINDS_TO="${IMPORT_DIR}/metabolites_to_proteins.csv" \
    --delimiter="," \
    --array-delimiter="|" \
    --id-type=STRING \
    --skip-bad-relationships=true \
    --skip-duplicate-nodes=true

echo "✅ Import Complete."

echo "🟢 Restarting Neo4j Service..."
sudo systemctl start neo4j || echo "Warning: Could not start neo4j via systemctl."

echo "🔍 Setting up Indexes..."
# Once the database is back up, we must create indexes via Cypher for the Streamlit dashboard queries.
# Wait for neo4j to start
sleep 15
cypher-shell -u neo4j -p admin123 "CREATE INDEX metabolite_id_index IF NOT EXISTS FOR (m:Metabolite) ON (m.metaboliteId);"
cypher-shell -u neo4j -p admin123 "CREATE INDEX metabolite_name_index IF NOT EXISTS FOR (m:Metabolite) ON (m.name);"

echo "🎉 Metabolomics Dimension Fully Integrated!"
