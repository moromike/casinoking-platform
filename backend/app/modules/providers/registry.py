import os

# For now, hardcoded registry of external providers
# In a real scenario, this would be stored in the DB
PROVIDERS = {
    "m-and-m-games": {
        "secret_key": os.environ.get("MANDM_SECRET_KEY", "dummy_secret_key").encode()
    }
}

def get_provider_secret(provider_id: str) -> bytes:
    provider = PROVIDERS.get(provider_id)
    if not provider:
        return None
    return provider["secret_key"]
