# 🧬 Plan for Expanding and Optimizing the Multi-Omics Knowledge Graph

This plan outlines the strategic roadmap for making the `knowledge-graph-organs` more powerful and useful, focusing specifically on adding new critical biological dimensions and scaling the underlying infrastructure to handle massive datasets.

## Phase 1: Expanding Data & Dimensions

To elevate the graph from its current 7 dimensions to a true comprehensive in-silico human model, we will integrate three massive, high-impact datasets:

### 1.1 Epigenomics Integration (DNA Methylation)
*   **Data Source:** DiseaseMeth or EWAS Atlas.
*   **Integration Point:** Adding nodes for `CpG Sites` and relationships like `METHYLATES` to existing Gene/Transcript nodes, and `ASSOCIATED_WITH` to Disease nodes.
*   **Pipeline Update:** Create extraction and cleaning scripts in `scripts/1_acquire` and `scripts/2_clean` for large-scale epigenetic flat files. Add a new ingestion module in `scripts/8_ultimate_integration`.

### 1.2 Metabolomics Integration (HMDB)
*   **Data Source:** Human Metabolome Database (HMDB).
*   **Integration Point:** Adding `Metabolite` nodes. Connecting them via `PRODUCED_BY` to Microbiome/Enzyme nodes, `BIOMARKER_FOR` to Disease nodes, and `TARGETED_BY` to Drug nodes.
*   **Pipeline Update:** Ingest HMDB XML/CSV structures. This connects the existing Gut-Microbiome axis directly to Phenomics (Diseases) via circulating metabolites.

### 1.3 3D Protein Structures (AlphaFold)
*   **Data Source:** AlphaFold Protein Structure Database (EBI).
*   **Integration Point:** Appending structural embeddings, pLDDT scores, and active site topologies to existing `Protein` (from STRING-DB/HPA) nodes.
*   **Pipeline Update:** Fetch and parse CIF/PDB files to extract structural metadata. This provides physical docking context for the existing `Pharmacology` dimension, moving beyond simple binary drug-target edges to structurally-aware edges.

---
## Phase 2: Performance & Scale Optimizations

Given the massive influx of data from Epigenomics (hundreds of millions of methylation sites), Metabolomics, and the structural complexity of AlphaFold, scaling the ingestion and graph querying infrastructure is mandatory to prevent out-of-memory (OOM) errors and slow traversals.

### 2.1 Integrating Apache Spark for Data Preprocessing
The existing Python pandas/CSV workflow in `scripts/2_clean` will become a bottleneck when cleaning and deduplicating billion-row epigenomic datasets.

*   **Action:** Introduce **PySpark** in `scripts/2_clean`.
*   **Implementation:** Replace massive in-memory pandas DataFrames with distributed Spark RDDs/DataFrames to generate the Neo4j ingestion triplets (Node-Edge-Node) as highly-compressed Parquet files. This ensures scalable ETL regardless of dataset size.

### 2.2 Optimizing Neo4j Ingestion (Bulk Import)
The current `scripts/3_graph/live_instantiate_bulk.py` relies on Cypher `UNWIND`. For billion-edge databases, this is suboptimal compared to the native import tool.

*   **Action:** Transition from transactional Cypher ingestion to **Neo4j Admin Import**.
*   **Implementation:** Refactor the graph instantiation scripts to output pure CSVs compliant with the `neo4j-admin database import` tool. This bypasses the transactional engine for the initial load, enabling the import of 1 billion edges in minutes instead of days.

### 2.3 Neo4j Database Tuning & Clustering
*   **Action:** Optimize Neo4j `neo4j.conf`.
*   **Implementation:**
    *   **Memory Tuning:** Explicitly allocate PageCache to hold the entire estimated graph size in RAM, minimizing disk I/O. Tune the JVM Heap size strictly to avoid costly garbage collection pauses during heavy Graph Neural Network traversals.
    *   **Indexing:** Implement composite B-tree indexing and specialized vector indexing (for AlphaFold structure embeddings) to ensure multi-hop query performance on the Streamlit dashboard remains sub-second.
    *   **Enterprise Architecture (Future Proofing):** Migrate from a single-node Community Edition to Neo4j Enterprise Edition clustered architecture (e.g., 3 Core members, 2 Read Replicas). This ensures high availability and scales read capacity, separating the heavy analytic workloads (like PageRank or GNN embedding generation) from the live Streamlit dashboard queries.
