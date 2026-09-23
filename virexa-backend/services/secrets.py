"""Central secrets loader: Azure Key Vault first, .env / App Settings fallback.

Slide gap being closed: "Azure Key Vault — No (secrets in .env / App
Settings — call this out as future work)". After this change the answer
is: Key Vault supported when AZURE_KEY_VAULT_URL is set, otherwise the
app keeps working on .env / App Settings (local dev + demo safe).

Usage:
    from services import secrets
    api_key = secrets.get("AZURE-OPENAI-API-KEY") or os.getenv("AZURE_OPENAI_API_KEY")

Key Vault secret names cannot contain underscores, so this module maps
ENV_VAR_NAME -> key-vault-name automatically (underscores become dashes).
Both spellings are tried, e.g. AZURE_OPENAI_API_KEY <-> AZURE-OPENAI-API-KEY.

Auth: DefaultAzureCredential (Managed Identity on Azure, Azure CLI /
VS Code credentials locally). No code change needed between local and
hosted — just set AZURE_KEY_VAULT_URL.
"""
from __future__ import annotations

import os

_vault_client = None
_vault_available: bool | None = None
_cache: dict[str, str | None] = {}


def key_vault_url() -> str | None:
    return os.getenv("AZURE_KEY_VAULT_URL")


def is_key_vault_configured() -> bool:
    return bool(key_vault_url())


def _get_client():
    """Lazily build a SecretClient. Returns None when not configured / no auth."""
    global _vault_client, _vault_available
    if _vault_available is not None:
        return _vault_client
    url = key_vault_url()
    if not url:
        _vault_available = False
        return None
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        _vault_client = SecretClient(vault_url=url, credential=DefaultAzureCredential())
        # Cheap probe: listing is not needed — just mark available. Real
        # errors surface per-secret in get() and fall back to env.
        _vault_available = True
        return _vault_client
    except Exception as e:
        print(f"[secrets] Key Vault unavailable, falling back to env: {e}")
        _vault_client = None
        _vault_available = False
        return None


def _candidate_names(env_name: str) -> list[str]:
    dashed = env_name.replace("_", "-")
    names = [dashed]
    if dashed != env_name:
        names.append(env_name)
    # Common alias without prefix differences
    return names


def get(env_name: str, default: str | None = None) -> str | None:
    """Get a secret: env var first (fast path), then Key Vault, then default.

    Env-first is intentional: local .env and App Settings keep working with
    zero latency; Key Vault is the production source of truth when those
    are unset.
    """
    if env_name in _cache:
        cached = _cache[env_name]
        return cached if cached is not None else default
    env_val = os.getenv(env_name)
    if env_val:
        _cache[env_name] = env_val
        return env_val
    client = _get_client()
    if client is not None:
        for name in _candidate_names(env_name):
            try:
                secret = client.get_secret(name)
                if secret and secret.value:
                    _cache[env_name] = secret.value
                    # Also export to env so legacy os.getenv call sites pick it up
                    os.environ[env_name] = secret.value
                    return secret.value
            except Exception:
                continue
    _cache[env_name] = None
    return default


def get_required(env_name: str) -> str:
    val = get(env_name)
    if not val:
        raise RuntimeError(
            f"{env_name} not set. Set it in .env / App Settings, "
            "or store it in Key Vault and set AZURE_KEY_VAULT_URL."
        )
    return val


def source(env_name: str) -> str:
    """Where would get() resolve this from? (no secret values leaked)."""
    if os.getenv(env_name):
        return "env"
    if is_key_vault_configured() and _get_client() is not None:
        return "key-vault"
    return "missing"


def status() -> dict:
    """Safe-to-expose diagnostics for GET /secrets/status."""
    tracked = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_STORAGE_CONNECTION_STRING",
        "COSMOS_KEY",
        "COSMOS_ENDPOINT",
        "AZURE_SEARCH_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SPEECH_KEY",
        "AZURE_SPEECH_REGION",
        "JWT_SECRET",
    ]
    return {
        "key_vault_configured": is_key_vault_configured(),
        "key_vault_url_set": bool(key_vault_url()),
        "mode": "key-vault" if is_key_vault_configured() else "env",
        "secrets": {name: {"source": source(name)} for name in tracked},
    }


def load_into_env(names: list[str] | None = None) -> dict[str, str]:
    """Best-effort warm-up: pull Key Vault values into os.environ.

    Called once at startup (see main.py). Never raises — a missing vault
    just means the app runs on .env / App Settings as before.
    """
    if names is None:
        names = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_STORAGE_CONNECTION_STRING",
            "COSMOS_KEY",
            "COSMOS_ENDPOINT",
            "AZURE_SEARCH_KEY",
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SPEECH_KEY",
            "AZURE_SPEECH_REGION",
        ]
    loaded: dict[str, str] = {}
    for name in names:
        try:
            val = get(name)
            if val:
                loaded[name] = "env" if os.getenv(name) else "key-vault"
        except Exception:
            continue
    return loaded
