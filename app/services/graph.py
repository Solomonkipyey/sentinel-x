import itertools

import networkx as nx
from sqlalchemy.orm import Session

from app.models import DocumentEntity, Entity


def build_graph(db: Session, min_weight: int = 1) -> nx.Graph:
    G = nx.Graph()
    rows = db.query(DocumentEntity).all()

    by_doc: dict[str, list[str]] = {}
    for r in rows:
        by_doc.setdefault(r.document_id, []).append(r.entity_id)

    # Only connect entities if they appear in the same document
    for ents in by_doc.values():
        for a, b in itertools.combinations(set(ents), 2):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)

    # Remove weak connections
    G.remove_edges_from(
        [(u, v) for u, v, w in G.edges(data="weight") if w < min_weight]
    )

    entities = {e.id: e for e in db.query(Entity).all()}
    for n in G.nodes:
        e = entities.get(n)
        if e:
            G.nodes[n]["kind"] = e.kind
            G.nodes[n]["value"] = e.value
            G.nodes[n]["risk"] = e.risk_score

    return G


def graph_to_json(G: nx.Graph) -> dict:
    return {
        "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes],
        "edges": [
            {"source": u, "target": v, **G[u][v]} for u, v in G.edges
        ],
    }