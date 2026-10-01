import pytest

from pepatlas.extract import build_graph
from pepatlas.reasoner import Engine


@pytest.fixture(scope="session")
def graph():
    return build_graph()


@pytest.fixture(scope="session")
def engine(graph):
    return Engine(graph)


def edge_types(graph, src, dst):
    return {e["type"] for e in graph.out(src) if e["dst"] == dst}
