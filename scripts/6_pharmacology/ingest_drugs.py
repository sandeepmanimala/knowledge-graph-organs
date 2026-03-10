import os
import pandas as pd
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "admin123")

def ingest_pharmacology():
    print("--- Phase 9: Drug Target Repurposing (Pharmacology Integration) ---")
    
    # 1. Mock FDA-approved drugs targeting specific proteins in our graph
    drugs_data = [
        {"drug_id": "DB00158", "name": "Folic Acid", "inhibits": "PROT_100"},
        {"drug_id": "DB01076", "name": "Atorvastatin", "inhibits": "PROT_500"},
        {"drug_id": "DB00564", "name": "Rosiglitazone", "inhibits": "ADIPOR1"},
        {"drug_id": "DB01115", "name": "Nifedipine", "inhibits": "INSR"},
        {"drug_id": "DBXYZ01", "name": "Experimental_Inhibitor_X", "inhibits": "Irisin"},
        {"drug_id": "DBXYZ02", "name": "Pancreatic_Blocker_Y", "inhibits": "Insulin"}
    ]
    
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            # Create Drug Node Constraint
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Drug) REQUIRE d.id IS UNIQUE")
            
            print("\n1. Ingesting Explicit (:Drug)-[:INHIBITS]->(:Protein) Edges...")
            for d in drugs_data:
                session.run("""
                    MERGE (drug:Drug {id: $id})
                    SET drug.name = $name
                    WITH drug
                    MATCH (protein:Protein {name: $protein_name})
                    MERGE (drug)-[:INHIBITS]->(protein)
                """, id=d['drug_id'], name=d['name'], protein_name=d['inhibits'])
            
            print("   -> Pharmacology mappings successfully injected into the multigraph.")

            print("\n2. Executing Therapeutic Queries...")
            print("-" * 60)
            print("Query A: Find all FDA-approved/Experimental drugs that inhibit the signaling cascade specifically starting from the Pancreas or Muscle_Skeletal")
            
            query = """
                MATCH path = (drug:Drug)-[:INHIBITS]->(protein:Protein)<-[:SECRETED_BY]-(source:Anatomy)
                WHERE source.name IN ['Pancreas', 'Muscle_Skeletal']
                RETURN drug.name AS Drug, protein.name AS Target, source.name AS OrganOrigin
            """
            result = session.run(query)
            for record in result:
                print(f" 💊 {record['Drug']} inhibits [{record['Target']}] (which is secreted by {record['OrganOrigin']})")
                
            print("\nQuery B: Find drugs that inhibit Receptors involved in communications targeting Liver or Adipose_Tissue")
            query_b = """
                MATCH (drug:Drug)-[:INHIBITS]->(receptor:Protein)-[:EXPRESSED_IN]->(target_tissue:Anatomy)
                WHERE target_tissue.name IN ['Liver', 'Adipose_Tissue']
                MATCH (messenger:Protein)-[:BINDS_TO]->(receptor)
                MATCH (source:Anatomy)-[:SECRETED_BY]->(messenger)
                RETURN drug.name AS Drug, receptor.name AS Receptor, target_tissue.name AS TargetOrgan, source.name AS SourceOrgan, messenger.name AS Messenger
            """
            result_b = session.run(query_b)
            for record in result_b:
                print(f" 🛡️ {record['Drug']} blocks the {record['Receptor']} receptor on {record['TargetOrgan']}")
                print(f"    -> Disrupting the {record['SourceOrgan']} --({record['Messenger']})--> {record['TargetOrgan']} pathway.")

if __name__ == "__main__":
    ingest_pharmacology()
