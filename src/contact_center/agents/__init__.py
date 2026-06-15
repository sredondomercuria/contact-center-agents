"""Agentes (nodos del grafo). Cada uno: recibe el estado, devuelve un dict parcial."""

from .classifier import classifier
from .critic import critic
from .producer import produce
from .responder import responder
from .retriever import retriever
from .router import router

__all__ = ["produce", "classifier", "retriever", "responder", "critic", "router"]
