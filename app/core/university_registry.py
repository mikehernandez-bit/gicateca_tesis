from app.universities.unac.provider import UNACProvider
from app.universities.uni.provider import UNIProvider

_PROVIDERS = {
    "unac": UNACProvider(),
    "uni": UNIProvider(),
}

def get_provider(code: str):
    code = (code or "unac").lower().strip()
    return _PROVIDERS.get(code, _PROVIDERS["unac"])
