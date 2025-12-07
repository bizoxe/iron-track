DEFAULT_USER_ROLE_SLUG = "application-access"
"""The slug of the default role assigned to all users."""
SUPERUSER_ROLE_SLUG = "superuser"
"""The slug of the superuser role."""
FITNESS_TRAINER_ROLE_SLUG = "fitness-trainer"
"""The slug of the fitness trainer role."""
USER_AUTH_CACHE_EXPIRE_SECONDS = 1800
"""The duration (in seconds) for which user authentication/authorization details are cached."""
DEFAULT_ADMIN_EMAIL = "system.admin@example.com"
"""Primary system admin email."""
ACCESS_TOKEN_MAX_AGE = 30 * 60  # must be consistent with JWT settings
""""The maximum duration (in seconds) that an access token is stored in a cookie.."""
REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60  # must be consistent with JWT settings
"""The maximum duration (in seconds) the refresh token is stored in the cookie and used for
the Redis blacklist expiry time."""
COOKIE_SECURE_VALUE = False
"""Boolean value for the 'secure' flag on authentication cookies (requires HTTPS)."""
FASTAPI_CACHE_PREFIX = "fastapi-cache"
"""Cache prefix for the fastapi-cache2 library."""
USER_AUTH_CACHE_PREFIX = "user_auth"
"""Cache prefix for authenticated/authorized user."""
