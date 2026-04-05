from data_layer_manager.core.config import GraphBackend, get_settings
from data_layer_manager.domain.interfaces.graph_store import BaseGraphStore
from data_layer_manager.infrastructure.graphstores.neo4j import Neo4jGraphStore


def get_graph_store() -> BaseGraphStore:
    """
    Returns the configured GraphStore implementation.
    """
    settings = get_settings()
    backend = settings.graph_store.backend

    if backend == GraphBackend.NEO4J:
        return Neo4jGraphStore()

    raise ValueError(f"Unsupported graph backend: {backend}")
