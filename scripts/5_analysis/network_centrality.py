import os
from neo4j import GraphDatabase
import pandas as pd

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "admin123")

def run_advanced_queries():
    print("--- Advanced Biological Graph Queries ---")
    
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            
            print("\n1. Top 5 Most Active Secreting Organs (Out-Degree Centrality of SECRETED_BY)")
            print("-" * 60)
            result = session.run("""
                MATCH (a:Anatomy)-[:SECRETED_BY]->(p:Protein)
                RETURN a.name AS organ, count(p) AS secreted_count
                ORDER BY secreted_count DESC
                LIMIT 5
            """)
            for record in result:
                print(f" 🏭 {record['organ']}: {record['secreted_count']} proteins secreted")

            print("\n2. Top 5 Most Targeted Organs (In-Degree Centrality of TARGETS_TISSUE)")
            print("-" * 60)
            result = session.run("""
                MATCH (p:Protein)-[:TARGETS_TISSUE]->(a:Anatomy)
                RETURN a.name AS organ, count(p) AS targeted_count
                ORDER BY targeted_count DESC
                LIMIT 5
            """)
            for record in result:
                print(f" 🎯 {record['organ']}: Targeted by {record['targeted_count']} distinct proteins")
                
            print("\n3. Longest/Most Complex Cascades (Transcript -> Protein -> Target Tissue)")
            print("-" * 60)
            # Querying a specific cascade from gene to target tissue
            # We'll limit to 3 examples
            result = session.run("""
                MATCH (g:Gene)-[:EXPRESSED_IN]->(src:Anatomy)-[:SECRETED_BY]->(p:Protein)-[:TARGETS_TISSUE]->(tgt:Anatomy)
                RETURN g.name AS gene, src.name AS source_organ, p.name AS protein, tgt.name AS target_organ
                LIMIT 3
            """)
            for idx, record in enumerate(result, 1):
                print(f" Cascade {idx}: [Gene: {record['gene']}] transcribes in [{record['source_organ']}]")
                print(f"             -> Secretes [{record['protein']}] -> Targets [{record['target_organ']}]")

if __name__ == "__main__":
    run_advanced_queries()
