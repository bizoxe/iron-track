# --- Business Logic & RBAC Slugs ---
DEFAULT_USER_ROLE_SLUG = "application-access"
"""The slug of the default role assigned to all users."""
SUPERUSER_ROLE_SLUG = "superuser"
"""The slug of the superuser role."""
FITNESS_TRAINER_ROLE_SLUG = "fitness-trainer"
"""The slug of the fitness trainer role."""

# --- Static Catalog Cache (Rarely Changed Data) ---
CATALOG_LIST_CACHE_TTL = "3m"
"""TTL for cached catalog lists with filters and sorting."""
CATALOG_ALL_CACHE_TTL = "3h"
"""TTL for full catalog tables cached as a single entity."""

# --- Argon2 Hashing Configuration ---
ARGON2_TIME_COST = 3
"""The number of iterations for the Argon2id hashing algorithm."""
ARGON2_MEMORY_COST = 65536
"""The amount of memory (in KiB) to be used by the Argon2id algorithm."""
ARGON2_PARALLELISM = 1
"""The number of parallel threads used during hashing."""
