import os
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "admin123")

def explore_graph():
    print("--- Exploring the Multi-Omics Knowledge Graph ---")
    
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            
            print("\n1. All Inter-Organ Communication Pathways:")
            print("-" * 60)
            result = session.run("""
                MATCH path = (source:Anatomy)-[:SECRETED_BY]->(protein:Protein)-[:TARGETS_TISSUE]->(target:Anatomy)
                RETURN source.name AS source_tissue, protein.name AS messenger, target.name AS target_tissue
            """)
            for record in result:
                print(f"🌲 [Tissue: {record['source_tissue']}] --secretes--> [{record['messenger']}] --targets--> [Tissue: {record['target_tissue']}]")

            print("\n2. Complex Multi-hop Routing Details (including Receptors and Transport):")
            print("-" * 60)
            result_complex = session.run("""
                MATCH (source:Anatomy)-[:SECRETED_BY]->(protein:Protein)
                MATCH (protein)-[:CIRCULATES_IN]->(transport:Anatomy)
                MATCH (protein)-[:BINDS_TO]->(receptor:Protein)
                MATCH (receptor)-[:EXPRESSED_IN]->(target:Anatomy)
                RETURN source.name AS src, protein.name AS prot, transport.name AS trans, 
                       receptor.name AS rec, target.name AS tgt
            """)
            for idx, record in enumerate(result_complex, 1):
                print(f"Path {idx}:")
                print(f"  Source:    {record['src']}")
                print(f"  Messenger: {record['prot']} (Circulates in {record['trans']})")
                print(f"  Receptor:  {record['rec']}")
                print(f"  Target:    {record['tgt']}\n")
                
            print("3. Count of entities in the graph:")
            print("-" * 60)
            counts = session.run("""
                MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count
            """)
            for record in counts:
                print(f" - {record['label']}: {record['count']}")

if __name__ == "__main__":
    explore_graph()
