# core/kg_builder.py
"""
Knowledge Graph builder for ImageAI.
Generates graph representations from structured OCR data.

Uses NetworkX for graph creation and manipulation.
"""
import networkx as nx
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.logger import log

# Output directory for graphs
GRAPH_OUTPUT_DIR = Path("examples/output")
GRAPH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_graph_from_fields(fields: Dict[str, Any], doc_name: str = "Document") -> nx.DiGraph:
    """
    Create a directed graph from structured fields.

    Args:
        fields: Dictionary of extracted fields
        doc_name: Name of the root document node

    Returns:
        nx.DiGraph: Directed graph representing the document structure
    """
    log.info(f"Building knowledge graph from fields: {list(fields.keys())}")
    
    G = nx.DiGraph()
    
    # Add root node
    G.add_node(doc_name, node_type="document", level=0)
    
    # Process each field
    for key, value in fields.items():
        _add_field_to_graph(G, doc_name, key, value, level=1)
    
    log.info(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G


def _add_field_to_graph(G: nx.DiGraph, parent: str, key: str, value: Any, level: int):
    """
    Recursively add fields to the graph.

    Args:
        G: NetworkX graph
        parent: Parent node name
        key: Field key
        value: Field value
        level: Depth level in the graph
    """
    # Create node name
    node_name = f"{key}"
    
    if isinstance(value, dict):
        # Add intermediate node for nested dict
        G.add_node(node_name, node_type="category", level=level, value=str(value))
        G.add_edge(parent, node_name, relationship="has_field")
        
        # Recursively add children
        for sub_key, sub_value in value.items():
            _add_field_to_graph(G, node_name, sub_key, sub_value, level + 1)
    
    elif isinstance(value, list):
        # Add intermediate node for list
        G.add_node(node_name, node_type="list", level=level, count=len(value))
        G.add_edge(parent, node_name, relationship="has_list")
        
        # Add list items
        for i, item in enumerate(value):
            if isinstance(item, dict):
                item_node = f"{key}_item_{i+1}"
                G.add_node(item_node, node_type="list_item", level=level + 1)
                G.add_edge(node_name, item_node, relationship="contains")
                
                for sub_key, sub_value in item.items():
                    _add_field_to_graph(G, item_node, sub_key, sub_value, level + 2)
            else:
                item_node = f"{key}_item_{i+1}"
                G.add_node(item_node, node_type="value", level=level + 1, value=str(item))
                G.add_edge(node_name, item_node, relationship="contains")
    
    else:
        # Add leaf node with value
        value_node = f"{key}"
        G.add_node(value_node, node_type="value", level=level, value=str(value))
        G.add_edge(parent, value_node, relationship="has_value")


def export_graph_json(graph: nx.DiGraph, output_path: Optional[str] = None) -> str:
    """
    Export graph as JSON.

    Args:
        graph: NetworkX graph
        output_path: Optional output file path

    Returns:
        str: Path to exported JSON file
    """
    if output_path is None:
        output_path = str(GRAPH_OUTPUT_DIR / "knowledge_graph.json")
    
    # Convert to node-link format
    data = nx.node_link_data(graph)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    log.info(f"Graph exported to JSON: {output_path}")
    return output_path


def export_graph_png(graph: nx.DiGraph, output_path: Optional[str] = None, figsize: tuple = (12, 8)) -> str:
    """
    Render and save graph as PNG using matplotlib.

    Args:
        graph: NetworkX graph
        output_path: Optional output file path
        figsize: Figure size (width, height)

    Returns:
        str: Path to exported PNG file
    """
    if output_path is None:
        output_path = str(GRAPH_OUTPUT_DIR / "knowledge_graph.png")
    
    plt.figure(figsize=figsize)
    
    # Use hierarchical layout
    pos = nx.spring_layout(graph, k=1, iterations=50)
    
    # Color nodes by type
    node_colors = []
    for node in graph.nodes():
        node_type = graph.nodes[node].get('node_type', 'unknown')
        if node_type == 'document':
            node_colors.append('#FF6B6B')  # Red
        elif node_type == 'category':
            node_colors.append('#4ECDC4')  # Teal
        elif node_type == 'list':
            node_colors.append('#45B7D1')  # Blue
        elif node_type == 'value':
            node_colors.append('#96CEB4')  # Green
        else:
            node_colors.append('#FFEAA7')  # Yellow
    
    # Draw graph
    nx.draw(graph, pos, 
            node_color=node_colors,
            node_size=2000,
            font_size=8,
            font_weight='bold',
            with_labels=True,
            arrows=True,
            edge_color='#95A5A6',
            arrowsize=20,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.1')
    
    plt.title("Knowledge Graph", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    log.info(f"Graph exported to PNG: {output_path}")
    return output_path


def get_graph_stats(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Get statistics about the graph.

    Args:
        graph: NetworkX graph

    Returns:
        dict: Statistics including node/edge counts, centrality metrics
    """
    stats = {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "is_directed": graph.is_directed(),
        "is_connected": nx.is_weakly_connected(graph) if graph.is_directed() else nx.is_connected(graph),
    }
    
    # Node types distribution
    node_types = {}
    for node in graph.nodes():
        node_type = graph.nodes[node].get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
    stats["node_types"] = node_types
    
    # Centrality (for small graphs)
    if graph.number_of_nodes() < 100:
        try:
            centrality = nx.degree_centrality(graph)
            top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_central_nodes"] = [{"node": node, "centrality": score} for node, score in top_nodes]
        except:
            pass
    
    log.info(f"Graph stats: {stats}")
    return stats


def create_invoice_graph(invoice_data: Dict[str, Any]) -> nx.DiGraph:
    """
    Create a specialized graph for invoice data.

    Args:
        invoice_data: Dictionary with invoice fields

    Returns:
        nx.DiGraph: Invoice knowledge graph
    """
    G = nx.DiGraph()
    
    # Root invoice node
    invoice_num = invoice_data.get('invoice_number', 'Unknown')
    G.add_node(f"Invoice_{invoice_num}", node_type="invoice", level=0)
    
    # Add invoice metadata
    for key in ['date', 'total', 'vendor', 'customer']:
        if key in invoice_data:
            node_name = f"{key}_{invoice_data[key]}"
            G.add_node(node_name, node_type="metadata", level=1, value=invoice_data[key])
            G.add_edge(f"Invoice_{invoice_num}", node_name, relationship=key)
    
    # Add line items
    if 'items' in invoice_data and isinstance(invoice_data['items'], list):
        items_node = "Items"
        G.add_node(items_node, node_type="items_list", level=1)
        G.add_edge(f"Invoice_{invoice_num}", items_node, relationship="contains")
        
        for i, item in enumerate(invoice_data['items']):
            item_node = f"Item_{i+1}"
            G.add_node(item_node, node_type="item", level=2)
            G.add_edge(items_node, item_node, relationship="has_item")
            
            if isinstance(item, dict):
                for key, value in item.items():
                    value_node = f"Item_{i+1}_{key}"
                    G.add_node(value_node, node_type="item_detail", level=3, value=str(value))
                    G.add_edge(item_node, value_node, relationship=key)
    
    log.info(f"Invoice graph created with {G.number_of_nodes()} nodes")
    return G
