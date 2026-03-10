import pandas as pd
import os
import json

def clean_and_normalize():
    raw_dir = "/Users/sandeepmanimala/.gemini/antigravity/scratch/multi_omics_kg/data/raw"
    clean_dir = "/Users/sandeepmanimala/.gemini/antigravity/scratch/multi_omics_kg/data/clean"
    os.makedirs(clean_dir, exist_ok=True)
    
    report = {
        "rows_dropped": 0,
        "entities_mapped": 0
    }
    
    # 1. Process GTEx
    gtex_file = os.path.join(raw_dir, "gtex_median_expression.csv")
    if os.path.exists(gtex_file):
        df_gtex = pd.read_csv(gtex_file)
        initial_len = len(df_gtex)
        df_gtex = df_gtex.dropna()
        report["rows_dropped"] += (initial_len - len(df_gtex))
        report["entities_mapped"] += len(df_gtex)
        
        # Nodes: Genes
        genes = df_gtex[['gencodeId', 'geneSymbol']].drop_duplicates().rename(columns={'gencodeId': 'id', 'geneSymbol': 'name'})
        genes['label'] = 'Gene'
        
        # Nodes: Anatomy
        anatomy = df_gtex[['tissueSiteDetailId']].drop_duplicates().rename(columns={'tissueSiteDetailId': 'id'})
        anatomy['name'] = anatomy['id']
        anatomy['label'] = 'Anatomy'
        
        # Edges: EXPRESSED_IN
        edges_gtex = df_gtex[['gencodeId', 'tissueSiteDetailId', 'median']].rename(columns={'gencodeId': 'source', 'tissueSiteDetailId': 'target'})
        edges_gtex['type'] = 'EXPRESSED_IN'
        edges_gtex['property_tpm'] = edges_gtex['median']
        edges_gtex = edges_gtex.drop(columns=['median'])
        
        genes.to_csv(os.path.join(clean_dir, "nodes_gene.csv"), index=False)
        anatomy.to_csv(os.path.join(clean_dir, "nodes_anatomy.csv"), index=False)
        edges_gtex.to_csv(os.path.join(clean_dir, "edges_expressed_in.csv"), index=False)

    # 2. Process HMDB
    hmdb_file = os.path.join(raw_dir, "hmdb_concentrations.csv")
    if os.path.exists(hmdb_file):
        df_hmdb = pd.read_csv(hmdb_file)
        initial_len = len(df_hmdb)
        df_hmdb = df_hmdb.dropna()
        report["rows_dropped"] += (initial_len - len(df_hmdb))
        
        # Conflict Resolution: Median concentration
        df_hmdb = df_hmdb.groupby(['hmdb_id', 'name', 'biofluid']).agg({'concentration_uM': 'median'}).reset_index()
        report["entities_mapped"] += len(df_hmdb)
        
        # Nodes: Metabolite
        metabolites = df_hmdb[['hmdb_id', 'name']].drop_duplicates().rename(columns={'hmdb_id': 'id'})
        metabolites['label'] = 'Metabolite'
        metabolites.to_csv(os.path.join(clean_dir, "nodes_metabolite.csv"), index=False)
        
        # Edges: CIRCULATES_IN
        edges_hmdb = df_hmdb[['hmdb_id', 'biofluid', 'concentration_uM']].rename(columns={'hmdb_id': 'source', 'biofluid': 'target'})
        edges_hmdb['type'] = 'CIRCULATES_IN'
        edges_hmdb['property_concentration_uM'] = edges_hmdb['concentration_uM']
        edges_hmdb = edges_hmdb.drop(columns=['concentration_uM'])
        edges_hmdb.to_csv(os.path.join(clean_dir, "edges_circulates_in_metabolite.csv"), index=False)

    # 3. Process HPA Secretome & Blood Atlas
    secretome_file = os.path.join(raw_dir, "secretome.tsv")
    blood_file = os.path.join(raw_dir, "blood_atlas.tsv")
    
    if os.path.exists(secretome_file) and os.path.exists(blood_file):
        df_sec = pd.read_csv(secretome_file, sep='\t')
        df_blood = pd.read_csv(blood_file, sep='\t')
        
        df_sec = df_sec.dropna()
        df_blood = df_blood.dropna()
        
        # Merge to get concentration for secreted proteins
        df_proteins = pd.merge(df_sec, df_blood, on=['Ensembl', 'Protein'], how='inner')
        report["entities_mapped"] += len(df_proteins)
        
        # Nodes: Protein
        proteins = df_proteins[['Ensembl', 'Protein']].drop_duplicates().rename(columns={'Ensembl': 'id', 'Protein': 'name'})
        proteins['label'] = 'Protein'
        proteins['is_secreted'] = True
        proteins.to_csv(os.path.join(clean_dir, "nodes_protein.csv"), index=False)

    # 4. Process IntiCom-DB
    inticom_file = os.path.join(raw_dir, "inticom_pathways.csv")
    if os.path.exists(inticom_file):
        df_inti = pd.read_csv(inticom_file)
        df_inti = df_inti.dropna()
        report["entities_mapped"] += len(df_inti)
        
        # Nodes: Receptors (as Proteins, simplified)
        receptors = df_inti[['receptor']].drop_duplicates()
        receptors = receptors[receptors['receptor'] != 'Unknown'].rename(columns={'receptor': 'name'})
        receptors['id'] = receptors['name'] + "_ID"
        receptors['label'] = 'Protein'
        receptors['is_secreted'] = False
        # Append to proteins if possible, or just save separate
        receptors.to_csv(os.path.join(clean_dir, "nodes_receptor.csv"), index=False)
        
        # We also have edges: SECRETED_BY, TARGETS_TISSUE
        # We will save the mapped inticom pathways so Phase 4 can build the correct multihop relationships
        df_inti.to_csv(os.path.join(clean_dir, "mapped_inticom.csv"), index=False)

    with open(os.path.join(clean_dir, "cleaning_report.json"), "w") as f:
        json.dump(report, f)
        
    print(f"Cleaning complete. Report: {report}")

if __name__ == "__main__":
    clean_and_normalize()
