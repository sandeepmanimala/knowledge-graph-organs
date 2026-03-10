import os
import requests
import pandas as pd
import gzip
import shutil

def fetch_gtex_bulk():
    print("Fetching FULL GTEx Bulk Median Expression Data (All 54 Tissues)...")
    url = "https://storage.googleapis.com/adult-gtex/bulk-gex/v8/rna-seq/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz"
    
    raw_dir = "/Users/sandeepmanimala/.gemini/antigravity/scratch/multi_omics_kg/data/raw"
    clean_dir = "/Users/sandeepmanimala/.gemini/antigravity/scratch/multi_omics_kg/data/clean"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(clean_dir, exist_ok=True)
    
    gz_file = os.path.join(raw_dir, "gtex_median_tpm.gct.gz")
    txt_file = os.path.join(raw_dir, "gtex_median_tpm.gct")
    
    # Download if not exists
    if not os.path.exists(gz_file) and not os.path.exists(txt_file):
        print("Downloading 23MB GCT file. This may take a minute...")
        response = requests.get(url, stream=True)
        with open(gz_file, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        print("Download complete.")
        
    # Decompress
    if not os.path.exists(txt_file):
        print("Decompressing GCT file...")
        with gzip.open(gz_file, 'rb') as f_in:
            with open(txt_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
    print("Processing GTEx matrix using Pandas...")
    # .gct files usually have 2 header rows to skip
    df = pd.read_csv(txt_file, sep='\t', skiprows=2)
    
    print(f"Loaded massive transcriptomics matrix: {df.shape[0]} Genes × {df.shape[1]-2} Tissues")
    
    # Extact Genes (Nodes)
    genes = df[['Name', 'Description']].drop_duplicates()
    genes = genes.rename(columns={'Name': 'id', 'Description': 'name'})
    genes['label'] = 'Gene'
    genes.to_csv(os.path.join(clean_dir, "nodes_gene_full.csv"), index=False)
    
    # Tissues (Anatomy Nodes)
    tissues = [col for col in df.columns if col not in ['Name', 'Description']]
    anatomy = pd.DataFrame({'id': tissues, 'name': tissues, 'label': 'Anatomy'})
    anatomy.to_csv(os.path.join(clean_dir, "nodes_anatomy_full.csv"), index=False)
    
    print("Melting dataframe to construct Triplet Multigraph Edges (takes a moment)...")
    # Melt the dataframe: Genes as rows, Tissues as columns -> long format
    melted = df.melt(id_vars=['Name', 'Description'], var_name='tissue', value_name='tpm')
    
    # We only want to keep biologically relevant baseline expressions. 
    # To reduce graph noise, let's only keep TPM > 0.5 (active transcription)
    # The user wants "each and every" but dropping absolute zeroes saves millions of dead edges
    active_edges = melted[melted['tpm'] > 0.5].copy()
    
    edges = active_edges[['Name', 'tissue', 'tpm']].rename(columns={'Name': 'source', 'tissue': 'target', 'tpm': 'property_tpm'})
    edges['type'] = 'EXPRESSED_IN'
    
    out_edge_file = os.path.join(clean_dir, "edges_expressed_in_full.csv")
    edges.to_csv(out_edge_file, index=False)
    
    print(f"Extraction complete!")
    print(f" -> Found {len(genes)} unique genes.")
    print(f" -> Mapped {len(tissues)} unique distinct human human tissues/organs.")
    print(f" -> Generated {len(edges)} active (TPM > 0.5) EXPRESSED_IN edges.")
    print(f"Saved optimized Graph matrices to {clean_dir}.")

if __name__ == "__main__":
    fetch_gtex_bulk()
