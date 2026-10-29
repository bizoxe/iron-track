# --- RBAC Slugs ---
DEFAULT_USER_ROLE_SLUG = "application-access"
"""Slug of the default role assigned to all users."""
SUPERUSER_ROLE_SLUG = "superuser"
"""Slug of the superuser role."""
FITNESS_TRAINER_ROLE_SLUG = "fitness-trainer"
"""Slug of the fitness trainer role."""

# --- Defaults ---
DEFAULT_ADMIN_EMAIL = "system.admin@example.com"
"""Primary system admin email."""
USER_AUTH_CACHE_KEY_PREFIX = "user_auth"
"""Prefix for cached user auth data, keyed by token subject."""

# --- Argon2 Hashing Configuration ---
ARGON2_TIME_COST = 3
"""Number of iterations for the Argon2id hashing algorithm."""
ARGON2_MEMORY_COST = 65536
"""Amount of memory (in KiB) used by the Argon2id algorithm."""
ARGON2_PARALLELISM = 1
"""Number of parallel threads used during hashing."""
