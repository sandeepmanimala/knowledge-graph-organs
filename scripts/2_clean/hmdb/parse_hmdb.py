"""
Script to parse the massive 5GB+ HMDB XML using lxml/iterparse (to prevent OOM errors).
It extracts `Metabolite` nodes and highly specific edges like `BINDS_TO` (Proteins) and `ASSOCIATED_WITH` (Diseases).
Outputs Neo4j Admin Import ready CSV headers.

Execution: python3 scripts/2_clean/hmdb/parse_hmdb.py
"""
import xml.etree.ElementTree as ET
import csv
from pathlib import Path

# Paths
INPUT_XML = Path("data/raw/hmdb/hmdb_metabolites.xml")
OUTPUT_DIR = Path("data/processed/hmdb/import")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Node CSV Paths (Neo4j Admin Import Headers)
NODES_CSV = OUTPUT_DIR / "metabolites_nodes.csv"
EDGES_DISEASE_CSV = OUTPUT_DIR / "metabolites_to_diseases.csv"
EDGES_PROTEIN_CSV = OUTPUT_DIR / "metabolites_to_proteins.csv"

# XML Namespace for HMDB
NS = {"hmdb": "http://www.hmdb.ca"}

def process_hmdb_xml():
    print(f"🧬 Parsing massive HMDB XML: {INPUT_XML}")

    # 1. Open Output CSV Writers with Neo4j Admin Import Headers
    # `neo4j-admin` requires explicit typings like `:ID`, `:LABEL`, `:START_ID`, `:END_ID`, `:TYPE`
    with open(NODES_CSV, mode="w", newline="", encoding="utf-8") as nf, \
         open(EDGES_DISEASE_CSV, mode="w", newline="", encoding="utf-8") as edf, \
         open(EDGES_PROTEIN_CSV, mode="w", newline="", encoding="utf-8") as epf:

        node_writer = csv.writer(nf)
        edge_disease_writer = csv.writer(edf)
        edge_protein_writer = csv.writer(epf)

        # Admin Import Headers
        node_writer.writerow(["metaboliteId:ID", "name", "chemical_formula", "cellular_location", ":LABEL"])
        edge_disease_writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        edge_protein_writer.writerow([":START_ID", ":END_ID", ":TYPE"])

        # 2. Iterparse the XML (Memory Efficient: processes element by element instead of loading full DOM)
        # Using `iterparse` ensures we don't crash the Python interpreter with a 5GB file
        context = ET.iterparse(INPUT_XML, events=("end",))
        count = 0

        for event, elem in context:
            # Match the closing tag of a metabolite
            if elem.tag.endswith("metabolite"):

                # Extract Core Attributes (handling namespaces)
                hmdb_id = elem.findtext("hmdb:accession", default="", namespaces=NS)
                name = elem.findtext("hmdb:name", default="", namespaces=NS)
                formula = elem.findtext("hmdb:chemical_formula", default="", namespaces=NS)

                # Extract Biological Properties (Cellular Location)
                locs_elem = elem.find("hmdb:biological_properties/hmdb:cellular_locations", namespaces=NS)
                location = "|".join([loc.text for loc in locs_elem.findall("hmdb:cellular_location", namespaces=NS)]) if locs_elem else ""

                # Write Node
                node_writer.writerow([hmdb_id, name, formula, location, "Metabolite"])

                # Extract Diseases (`ASSOCIATED_WITH` DisGeNet nodes)
                diseases_elem = elem.find("hmdb:diseases", namespaces=NS)
                if diseases_elem:
                    for d in diseases_elem.findall("hmdb:disease", namespaces=NS):
                        disease_name = d.findtext("hmdb:name", default="", namespaces=NS)
                        if disease_name:
                            edge_disease_writer.writerow([hmdb_id, disease_name, "ASSOCIATED_WITH_DISEASE"])

                # Extract Proteins (`BINDS_TO` Uniprot/STRING nodes)
                proteins_elem = elem.find("hmdb:protein_associations", namespaces=NS)
                if proteins_elem:
                    for p in proteins_elem.findall("hmdb:protein", namespaces=NS):
                        uniprot_id = p.findtext("hmdb:uniprot_id", default="", namespaces=NS)
                        if uniprot_id:
                            edge_protein_writer.writerow([hmdb_id, uniprot_id, "BINDS_TO"])

                count += 1
                if count % 10000 == 0:
                    print(f"Processed {count} metabolites...")

                # 3. Clear the element from memory to prevent RAM exhaustion
                elem.clear()

        print(f"✅ Finished parsing {count} total metabolites.")

if __name__ == "__main__":
    if not INPUT_XML.exists():
        print(f"❌ Error: {INPUT_XML} not found. Run the acquire script first.")
    else:
        process_hmdb_xml()
