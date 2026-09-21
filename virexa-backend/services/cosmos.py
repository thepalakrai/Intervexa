import os
from azure.cosmos import CosmosClient, PartitionKey
from typing import Optional

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DATABASE", "virexa")
USERS_CONTAINER = os.getenv("COSMOS_CONTAINER_USERS", "users")
SESSIONS_CONTAINER = os.getenv("COSMOS_CONTAINER_SESSIONS", "sessions")
EVALUATIONS_CONTAINER = os.getenv("COSMOS_CONTAINER_EVALUATIONS", "evaluations")

_client = None


def get_client() -> CosmosClient:
    global _client
    if _client is None:
        if not COSMOS_ENDPOINT or not COSMOS_KEY:
            raise RuntimeError("COSMOS_ENDPOINT / COSMOS_KEY not set. Check your .env file.")
        _client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    return _client


def get_sessions_container():
    db = get_client().get_database_client(DATABASE_NAME)
    return db.get_container_client(SESSIONS_CONTAINER)


def get_evaluations_container():
    db = get_client().get_database_client(DATABASE_NAME)
    return db.get_container_client(EVALUATIONS_CONTAINER)


def get_users_container():
    db = get_client().get_database_client(DATABASE_NAME)
    return db.get_container_client(USERS_CONTAINER)


def create_user(user_dict: dict) -> dict:
    """user_dict must include 'id' and 'email' (partition key)."""
    container = get_users_container()
    return container.create_item(body=user_dict)


def get_user_by_email(email: str) -> Optional[dict]:
    container = get_users_container()
    query = "SELECT * FROM c WHERE c.email = @email"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@email", "value": email}],
        partition_key=email,
    ))
    return items[0] if items else None


def create_session(session_dict: dict) -> dict:
    """
    session_dict must include 'id' and 'candidateId' (partition key).
    """
    container = get_sessions_container()
    return container.create_item(body=session_dict)


def get_session(session_id: str, candidate_id: str) -> Optional[dict]:
    container = get_sessions_container()
    try:
        return container.read_item(item=session_id, partition_key=candidate_id)
    except Exception as e:
        print(f"[cosmos.get_session] Real error (was being hidden): {type(e).__name__}: {e}")
        return None


def update_session(session_dict: dict) -> dict:
    container = get_sessions_container()
    return container.upsert_item(body=session_dict)


def save_evaluation(evaluation_dict: dict) -> dict:
    """
    evaluation_dict must include 'id' and 'candidateId' (partition key).
    """
    container = get_evaluations_container()
    return container.create_item(body=evaluation_dict)


def get_evaluations_for_candidate(candidate_id: str) -> list[dict]:
    container = get_evaluations_container()
    query = "SELECT * FROM c WHERE c.candidateId = @candidateId"
    items = container.query_items(
        query=query,
        parameters=[{"name": "@candidateId", "value": candidate_id}],
        partition_key=candidate_id,
    )
    return list(items)
