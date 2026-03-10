import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
from streamlit_agraph import agraph, Node, Edge, Config

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "admin123")

st.set_page_config(page_title="Multi-Omics Knowledge Graph", layout="wide")
st.title("Hierarchical Multi-Omics Knowledge Graph (Systemic Inter-Organ Communication)")
st.markdown("Explore the multi-omics topology dynamically querying the local Neo4j full-scale database.")

@st.cache_resource
def init_driver():
    return GraphDatabase.driver(URI, auth=AUTH)

try:
    driver = init_driver()
except Exception as e:
    st.error(f"Failed to connect to Neo4j. Is the database running? {str(e)}")
    st.stop()

st.sidebar.header("Graph Filters")

def get_all_tissues():
    with driver.session() as session:
        result = session.run("MATCH (a:Anatomy) RETURN a.name AS name ORDER BY a.name")
        return [record["name"] for record in result]

tissues = get_all_tissues()
target_tissue = st.sidebar.selectbox("Select Tissue/Organ to Analyze", tissues)
limit = st.sidebar.slider("Edge Limit", min_value=10, max_value=200, value=50)

# Cypher querying capability
def get_subgraph(target_tissue, limit):
    nodes = []
    edges = []
    node_set = set()
    
    query = """
    MATCH path = (source:Anatomy)-[:SECRETED_BY]->(p:Protein)-[:TARGETS_TISSUE]->(target:Anatomy)
    WHERE target.name = $tissue OR source.name = $tissue
    RETURN source, p, target
    LIMIT $limit
    """
    
    # We will also pull any drugs inhibiting these proteins natively
    query_drugs = """
    MATCH (d:Drug)-[:INHIBITS]->(p:Protein)<-[:SECRETED_BY]-(a:Anatomy)
    WHERE a.name = $tissue OR p.name IN ['Insulin', 'Adiponectin', 'ADIPOR1', 'INSR', 'Irisin']
    RETURN d, p
    LIMIT $limit
    """

    with driver.session() as session:
        result = session.run(query, tissue=target_tissue, limit=limit)
        for record in result:
            src = record["source"]
            prot = record["p"]
            tgt = record["target"]
            
            if src['name'] not in node_set:
                nodes.append(Node(id=src['name'], label=src['name'], size=25, color="#FF6B6B")) # Red for source
                node_set.add(src['name'])
            if prot['name'] not in node_set:
                nodes.append(Node(id=prot['name'], label=prot['name'], size=15, color="#4ECDC4")) # Teal for protein
                node_set.add(prot['name'])
            if tgt['name'] not in node_set:
                nodes.append(Node(id=tgt['name'], label=tgt['name'], size=25, color="#FFE66D")) # Yellow for target
                node_set.add(tgt['name'])
                
            edges.append(Edge(source=src['name'], target=prot['name'], label="SECRETED_BY"))
            edges.append(Edge(source=prot['name'], target=tgt['name'], label="TARGETS_TISSUE"))
            
        res_drugs = session.run(query_drugs, tissue=target_tissue, limit=limit)
        for record in res_drugs:
            drug = record['d']
            prot = record['p']
            if drug['name'] not in node_set:
                nodes.append(Node(id=drug['name'], label=drug['name'], size=20, color="#845EC2", shape="star")) # Purple for drug
                node_set.add(drug['name'])
            if prot['name'] not in node_set:
                nodes.append(Node(id=prot['name'], label=prot['name'], size=15, color="#4ECDC4"))
                node_set.add(prot['name'])
            
            edges.append(Edge(source=drug['name'], target=prot['name'], label="INHIBITS"))

    return nodes, edges

st.subheader(f"Systemic Routes passing through {target_tissue}")
nodes, edges = get_subgraph(target_tissue, limit)

config = Config(width=1000,
                height=600,
                directed=True, 
                physics=True, 
                hierarchical=False,
                nodeHighlightBehavior=True,
                highlightColor="#F7A7A6",
                collapsible=True)

if nodes:
    return_value = agraph(nodes=nodes, edges=edges, config=config)
    st.success(f"Rendered {len(nodes)} entities and {len(edges)} cross-tissue multi-omics edges.")
else:
    st.warning("No interactions found for this specific query on the current sampled graph structure.")

st.markdown("---")
st.markdown("Built by Google Antigravity Agentic Pipeline.")
