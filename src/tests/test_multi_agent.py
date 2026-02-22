"""Test ADK app and agent graph."""

import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)


def test_imports():
    from src import app, create_app, FACTUALITY_FACTORS

    assert app is not None
    assert len(FACTUALITY_FACTORS) == 6


def test_agent_creation():
    from src import create_app

    a = create_app()
    assert a.name == "factuality_evaluator"
    assert a.root_agent is not None


if __name__ == "__main__":
    test_imports()
    test_agent_creation()
    print("OK")
