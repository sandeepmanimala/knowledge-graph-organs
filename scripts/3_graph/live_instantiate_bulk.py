import os
import pandas as pd
from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "admin123")

def populate_live_db_bulk():
    print("Connecting to Live Neo4j instance at", URI)
    clean_dir = "/Users/sandeepmanimala/.gemini/antigravity/scratch/multi_omics_kg/data/clean"
    
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        # Clear old mock data to avoid conflicts with full set
        print("Clearing old mock database state...")
        driver.execute_query("MATCH (n) DETACH DELETE n")
        
        with driver.session() as session:
            # 1. Constraints
            print("Enforcing uniqueness constraints...")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (g:Gene) REQUIRE g.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Protein) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Anatomy) REQUIRE a.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Metabolite) REQUIRE m.id IS UNIQUE")
            
        # Helper for batch unwinding
        def execute_batch(query, records, batch_size=10000):
            with driver.session() as session:
                for i in range(0, len(records), batch_size):
                    batch = records[i:i+batch_size]
                    session.run(query, batch=batch)
                    
        # 2. Nodes
        print("Ingesting base nodes in batches...")
        
        # Anatomy (54 tissues)
        df_anato = pd.read_csv(os.path.join(clean_dir, "nodes_anatomy_full.csv"))
        execute_batch("UNWIND $batch AS row MERGE (a:Anatomy {id: row.id}) SET a.name = row.name", df_anato.to_dict('records'))
        
        # Protein
        df_prot = pd.read_csv(os.path.join(clean_dir, "nodes_protein_full.csv"))
        execute_batch("UNWIND $batch AS row MERGE (p:Protein {id: row.id}) SET p.name = row.name, p.is_secreted = row.is_secreted", df_prot.to_dict('records'))
        
        # Metabolite
        df_meta = pd.read_csv(os.path.join(clean_dir, "nodes_metabolite_full.csv"))
        execute_batch("UNWIND $batch AS row MERGE (m:Metabolite {id: row.id}) SET m.name = row.name", df_meta.to_dict('records'))
        
        # Gene
        df_gene = pd.read_csv(os.path.join(clean_dir, "nodes_gene_full.csv"))
        execute_batch("UNWIND $batch AS row MERGE (g:Gene {id: row.id}) SET g.name = row.name", df_gene.to_dict('records'))
        
        # 3. Edges
        print("Ingesting >100,000 Metabolite pathways...")
        df_circ = pd.read_csv(os.path.join(clean_dir, "edges_circulates_in_metabolite_full.csv"))
        execute_batch("""
            UNWIND $batch AS row 
            MATCH (source:Metabolite {id: row.source})
            MERGE (target:Anatomy {name: row.target})
            MERGE (source)-[r:CIRCULATES_IN]->(target)
            SET r.property_concentration_uM = toFloat(row.property_concentration_uM)
        """, df_circ.to_dict('records'))

        # GTEx Transcripts (~1M edges)
        print("Ingesting >1M GTEx Baseline Transcriptomics edges (Takes ~30 seconds)...")
        df_expr = pd.read_csv(os.path.join(clean_dir, "edges_expressed_in_full.csv"))
        execute_batch("""
            UNWIND $batch AS row 
            MATCH (source:Gene {id: row.source})
            MATCH (target:Anatomy {id: row.target})
            MERGE (source)-[r:EXPRESSED_IN]->(target)
            SET r.property_tpm = toFloat(row.property_tpm)
        """, df_expr.to_dict('records'), batch_size=50000)

        # IntiCom
        print("Mapping IntiCom Multi-Hop Systemic Routes...")
        df_inti = pd.read_csv(os.path.join(clean_dir, "mapped_inticom_full.csv"))
        execute_batch("""
            UNWIND $batch AS row 
            MERGE (source:Anatomy {name: row.source_tissue})
            MERGE (protein:Protein {name: row.secreted_protein})
            MERGE (source)-[:SECRETED_BY]->(protein)
            
            MERGE (transport:Anatomy {name: row.transport})
            MERGE (protein)-[:CIRCULATES_IN]->(transport)
            
            MERGE (target:Anatomy {name: row.target_tissue})
            MERGE (receptor:Protein {name: row.receptor})
            MERGE (protein)-[:TARGETS_TISSUE]->(target)
            MERGE (protein)-[:BINDS_TO]->(receptor)
            MERGE (receptor)-[:EXPRESSED_IN]->(target)
        """, df_inti.to_dict('records'))
                     
        print("-" * 50)
        print("SUCCESS: Live Neo4j Full-Scale Database (All Organs) Instantiated.")
        
        with driver.session() as session:
            print("\nFinal Database Scale Constraints:")
            for record in session.run("MATCH (n) RETURN labels(n)[0] AS Entity, count(n) AS InstanceCount"):
                print(f" - {record['Entity']}: {record['InstanceCount']:,}")
            
            edges = session.run("MATCH ()-[r]->() RETURN type(r) AS Edge, count(r) AS EdgeCount")
            for record in edges:
                 print(f" - [Edge] {record['Edge']}: {record['EdgeCount']:,}")

if __name__ == "__main__":
    populate_live_db_bulk()
