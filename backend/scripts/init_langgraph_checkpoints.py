"""Operator-only initialization. Creates dedicated LangGraph checkpoint tables.

Run only after reviewing permissions and taking a verified Postgres backup:
  cd backend
  LANGGRAPH_STRICT_MSGPACK=true python -m scripts.init_langgraph_checkpoints
"""
import os

from langgraph.checkpoint.postgres import PostgresSaver
from v2.agent_api import checkpoint_uri


def main():
    if os.environ.get("LANGGRAPH_STRICT_MSGPACK", "").lower() not in ("true", "1"):
        raise RuntimeError("Set LANGGRAPH_STRICT_MSGPACK=true before initializing checkpoints")
    with PostgresSaver.from_conn_string(checkpoint_uri()) as saver:
        saver.setup()
    print("LangGraph PostgreSQL checkpointer initialized")


if __name__ == "__main__":
    main()
