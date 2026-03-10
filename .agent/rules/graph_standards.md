---
description: Global standards for Multi-Omics Knowledge Graph
---

# Multi-Omics Inter-Organ Knowledge Graph Standards

1.  **Strict Typing**: All Python code must use strict type hints (e.g., `def process_data(df: pd.DataFrame) -> pd.DataFrame:`).
2.  **Data Manipulation**: The `pandas` library MUST be used for all dataframe and tabular data manipulations.
3.  **Safety Constraints**: Destructive terminal commands (such as `rm -rf`, `drop table`, etc.) are strictly PROHIBITED to prevent accidental data loss in the knowledge graph pipeline.
