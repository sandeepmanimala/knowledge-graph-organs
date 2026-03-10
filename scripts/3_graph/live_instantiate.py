import os
import pandas as pd
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "admin123")

def populate_live_db():
    clean_dir = "/Users/sandeepmanimala/.gemini/antigravity/scratch/multi_omics_kg/data/clean"
    
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to Live Neo4j instance at", URI)
        
        with driver.session() as session:
            # 1. Constraints
            print("Enforcing uniqueness constraints...")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (g:Gene) REQUIRE g.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Protein) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Anatomy) REQUIRE a.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Metabolite) REQUIRE m.id IS UNIQUE")
            
            # 2. Base Nodes
            print("Ingesting base nodes...")
            
            # Anatomy
            df_anatomy = pd.read_csv(os.path.join(clean_dir, "nodes_anatomy.csv"))
            for _, row in df_anatomy.iterrows():
                session.run("MERGE (a:Anatomy {id: $id}) SET a.name = $name", id=row['id'], name=row['name'])
                
            # Protein
            df_protein = pd.read_csv(os.path.join(clean_dir, "nodes_protein.csv"))
            for _, row in df_protein.iterrows():
                is_secreted = True if str(row['is_secreted']).lower() == 'true' else False
                session.run("MERGE (p:Protein {id: $id}) SET p.name = $name, p.is_secreted = $sec", 
                            id=row['id'], name=row['name'], sec=is_secreted)
                            
            # Receptor (simplified as Protein)
            df_receptor = pd.read_csv(os.path.join(clean_dir, "nodes_receptor.csv"))
            for _, row in df_receptor.iterrows():
                session.run("MERGE (p:Protein {id: $id}) SET p.name = $name", 
                            id=row['id'], name=row['name'])
                            
            # Gene
            df_gene = pd.read_csv(os.path.join(clean_dir, "nodes_gene.csv"))
            for _, row in df_gene.iterrows():
                session.run("MERGE (g:Gene {id: $id}) SET g.name = $name", 
                            id=row['id'], name=row['name'])
                            
            # Metabolite
            df_meta = pd.read_csv(os.path.join(clean_dir, "nodes_metabolite.csv"))
            for _, row in df_meta.iterrows():
                session.run("MERGE (m:Metabolite {id: $id}) SET m.name = $name", 
                            id=row['id'], name=row['name'])

            # 3. Edges
            print("Ingesting edges...")
            
            df_expr = pd.read_csv(os.path.join(clean_dir, "edges_expressed_in.csv"))
            for _, row in df_expr.iterrows():
                session.run("""
                    MATCH (source:Gene {id: $source_id})
                    MATCH (target:Anatomy {id: $target_id})
                    MERGE (source)-[r:EXPRESSED_IN]->(target)
                    SET r.property_tpm = $tpm
                """, source_id=row['source'], target_id=row['target'], tpm=row['property_tpm'])
                
            df_circ = pd.read_csv(os.path.join(clean_dir, "edges_circulates_in_metabolite.csv"))
            for _, row in df_circ.iterrows():
                session.run("""
                    MATCH (source:Metabolite {id: $source_id})
                    MERGE (target:Anatomy {name: $bio_name}) // Assume biofluid is Anatomy medium
                    MERGE (source)-[r:CIRCULATES_IN]->(target)
                    SET r.property_concentration_uM = $conc
                """, source_id=row['source'], bio_name=row['target'], conc=row['property_concentration_uM'])
                
            # 4. IntiCom Routing
            print("Mapping systemic routing protocols...")
            df_inti = pd.read_csv(os.path.join(clean_dir, "mapped_inticom.csv"))
            for _, row in df_inti.iterrows():
                session.run("""
                    MERGE (source:Anatomy {name: $source_name})
                    MERGE (protein:Protein {name: $protein_name})
                    MERGE (source)-[:SECRETED_BY]->(protein)
                    
                    MERGE (transport:Anatomy {name: $transport_name})
                    MERGE (protein)-[:CIRCULATES_IN]->(transport)
                    
                    MERGE (target:Anatomy {name: $target_name})
                    MERGE (receptor:Protein {name: $receptor_name})
                    MERGE (protein)-[:TARGETS_TISSUE]->(target)
                    MERGE (protein)-[:BINDS_TO]->(receptor)
                    MERGE (receptor)-[:EXPRESSED_IN]->(target)
                """, source_name=row['source_tissue'], protein_name=row['secreted_protein'], 
                     transport_name=row['transport'], target_name=row['target_tissue'],
                     receptor_name=row['receptor'])
                     
            print("SUCCESS: Live Neo4j database instantiated and enriched.")
            
            # Run test query
            result = session.run("MATCH (a:Anatomy)-[r:SECRETED_BY]->(p:Protein) RETURN a.name AS tissue, p.name AS protein LIMIT 5")
            records = list(result)
            print("\nValidation Sample Query [SECRETED_BY]:")
            for record in records:
                print(f" -> Tissue: {record['tissue']} secretes Protein: {record['protein']}")

if __name__ == "__main__":
    populate_live_db()
