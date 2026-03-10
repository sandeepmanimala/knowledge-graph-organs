---
description: Automated Monthly Data Refresh for the Multi-Omics Knowledge Graph
---
# Data Refresh Workflow

This agentic workflow automates the monthly polling of the GTEx, HPA, and HMDB repositories. When new datasets are released, the Antigravity agent will automatically fetch, clean, and merge the new multi-omics nodes and edges directly into the live Neo4j database. 

## Steps
1. Navigate to `/Users/sandeepmanimala/.gemini/antigravity/scratch/multi_omics_kg/`.
// turbo
2. Execute the data acquisition scripts to pull the latest differential datasets.
`python3 scripts/1_acquire/fetch_gtex_full.py && python3 scripts/1_acquire/fetch_other_full.py`
// turbo
3. Run the cleaning and semantic normalization pipeline using pandas.
`python3 scripts/2_clean/clean_full.py`
4. Request user review for the updated data matrices located in `data/clean/` before continuing.
// turbo
5. Re-run the bulk Cypher instantiation pipeline to execute `UNWIND MERGE` into the live Neo4j graph.
`python3 scripts/3_graph/live_instantiate_bulk.py`
6. Create an updated `Walkthrough` artifact proving that the graph data was refreshed successfully.
