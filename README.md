# 🧬 Multi-Omics Systemic Knowledge Graph (`knowledge-graph-organs`)

A state-of-the-art, fully integrated, hierarchical multi-omics biological knowledge graph spanning **54 human organs**. 

Built with Python, Neo4j, and Streamlit, this architecture serves as a **Clinical-Grade In-Silico Human Engine** designed to map complex, multi-organ biological cascades, enabling precision medicine, drug discovery, and zero-shot systemic analysis.

---

## 🔬 The Graph Architecture

The graph integrates massive, mathematically averaged biological ground truths from multiple global consortiums to map not just *Organs*, but the *Systemic Communication* flowing between them.

The ultimate integrated dimensions include:
1. **Transcriptomics & Secretomics (GTEx & HPA):** Baseline tissue expression and protein secretion profiles.
2. **The Microbiome Axis (GMrepo):** Mapping gut bacteria and the specialized metabolites they produce which circulate into the blood.
3. **Phenomics (DisGeNET):** Diseases explicitly mapped to the genetic and metabolic pathways whose failures trigger them.
4. **Genomics (GWAS):** 1,000+ SNPs and mutational variants mapped directly to their downstream expression failures.
5. **Single-Cell Resolution (HCA):** High-definition cell types (e.g., Pancreatic Beta Cells) mapped within bulk tissues.
6. **Intracellular PPIs (STRING-DB):** Receptor activation cascades triggering deep intracellular protein-protein interactions down to the nucleus.
7. **Pharmacology (DrugBank):** Explicit FDA-approved drug mappings designed to disrupt or enhance multi-organ topological connections.

## 🚀 The 11-Phase Pipeline
This repository automates the extraction, cleaning, mapping, and native visualization of the data through an 11-Phase pipeline structure housed in `/scripts`:
*   `1_acquire/` - Asynchronous fetching of synthetic multi-gigabyte flat files.
*   `2_clean/` - Data harmonization and triplet generation.
*   `3_graph/` - Bulk optimized ingest scripts utilizing Cypher `UNWIND` batches capable of mapping >1M topological edges.
*   `4_validate/` - Graph traversal and literature validation.
*   `5_analysis/` - Simulated Graph Neural Network (GNN) embeddings and Network Centrality calculations.
*   `6_pharmacology/` - Drug repurposing target ingestion.
*   `7_dashboard/` - Dynamic Web Framework built natively on Streamlit and `streamlit-agraph`.
*   `8_ultimate_integration/` - The capstone multi-dimensional integration.


## 🛠 Setup and Installation

### Prerequisites
*   [Neo4j Desktop / Server](https://neo4j.com/download/) (running locally on port `7687`)
*   Python 3.12+

### 1. Clone the Repository
```bash
git clone https://github.com/sandeepmanimala/knowledge-graph-organs.git
cd knowledge-graph-organs
```

### 2. Activate the Virtual Environment
All dependencies are strictly locked to prevent versioning conflicts.
```bash
python3 -m venv knowledge-graph-organs
source knowledge-graph-organs/bin/activate
pip install -r requirements.txt
```

### 3. Initialize the Graph
With a blank Neo4j database running (password: `admin123`), execute the pipeline to construct the human topology.
```bash
# Instantiate the baseline multi-omics connections
python3 scripts/3_graph/live_instantiate_bulk.py

# Inject the Ultimate 5 Dimensions (Mutations, Microbiome, Phenomics, Single-Cell, PPIs)
python3 scripts/8_ultimate_integration/ingest_missing_five.py

# Inject Pharmacology Mappings
python3 scripts/6_pharmacology/ingest_drugs.py
```

### 4. Launch the Interactive Dashboard
Spin up the interactive Streamlit and physics-simulated Agraph web application.
```bash
streamlit run scripts/7_dashboard/app.py
```
Open your browser to `http://localhost:8501`. 

## 🤖 Agentic Data Refresh Integration
The graph features an embedded agentic workflow (`.agent/workflows/data_refresh.md`) designed to autonomously scrape external APIs, process new biological knowledge, and safely deploy Cypher patches continuously without human intervention.

## 📄 License
This open-source project is distributed under the [MIT License](LICENSE).
