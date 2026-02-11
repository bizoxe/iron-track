DEFAULT_USER_ROLE_SLUG = "application-access"
"""The slug of the default role assigned to all users."""
SUPERUSER_ROLE_SLUG = "superuser"
"""The slug of the superuser role."""
FITNESS_TRAINER_ROLE_SLUG = "fitness-trainer"
"""The slug of the fitness trainer role."""
USER_AUTH_CACHE_TTL = "30m"
"""TTL for cached user authentication and authorization data."""
DEFAULT_ADMIN_EMAIL = "system.admin@example.com"
"""Primary system admin email."""
ACCESS_TOKEN_MAX_AGE = 30 * 60  # must be consistent with JWT settings
""""The maximum duration (in seconds) that an access token is stored in a cookie.."""
REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60  # must be consistent with JWT settings
"""The maximum duration (in seconds) the refresh token is stored in the cookie and used for
the Redis blacklist expiry time."""
COOKIE_SECURE_VALUE = False
"""Boolean value for the 'secure' flag on authentication cookies (requires HTTPS)."""
CATALOG_LIST_CACHE_TTL = "3m"
"""TTL for cached catalog lists with filters and sorting."""
CATALOG_ALL_CACHE_TTL = "3h"
"""TTL for full catalog tables cached as a single entity."""
# --- Argon2 Hashing Configuration ---
ARGON2_TIME_COST = 3
"""The number of iterations for the Argon2id hashing algorithm."""
ARGON2_MEMORY_COST = 65536
"""The amount of memory (in KiB) to be used by the Argon2id algorithm."""
ARGON2_PARALLELISM = 1  # set to 1 to minimize core contention on multi-core systems
"""The number of parallel threads used during hashing."""
