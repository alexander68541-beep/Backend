from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory limiter for now. Phase 8 will move this to Redis for multi-instance limits.
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
