from slowapi import Limiter
from slowapi.util import get_remote_address

# headers_enabled stays OFF: with it on, slowapi tries to inject X-RateLimit-* headers
# and then requires every limited endpoint to accept a `response: Response` param,
# raising "parameter `response` must be an instance of ..." otherwise. Limiting still
# works fully without the headers. Phase 8 will move this to Redis for multi-instance.
limiter = Limiter(key_func=get_remote_address)
