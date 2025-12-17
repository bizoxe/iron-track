JWT Utilities
=============

.. function:: encode_jwt(payload, private_key, algorithm, expire_minutes, expire_timedelta)
   :module: app.lib.jwt_utils

   Encode a JWT based on the provided payload and expiration settings.

   This function adds standard claims: 'iat' (issued at), 'exp' (expiration), and 'jti' (JWT ID) to the token payload before encoding.

   **Parameters:**

   * **payload** (*dict*) – The base data to include in the token (e.g., user ID, email).
   * **private_key** (*str*) – The private key used for signing the token. Defaults to the application’s configured private key.
   * **algorithm** (*str*) – The cryptographic algorithm used for signing (e.g., ‘RS256’). Defaults to the configured algorithm.
   * **expire_minutes** (*int*) – The token’s lifespan in minutes, used only if ``expire_timedelta`` is not provided.
   * **expire_timedelta** (*timedelta | None*) – Explicit timedelta defining the token’s total lifespan. Overrides ``expire_minutes``. Used primarily for Refresh Tokens.

   **Returns:**

   * *str* – The encoded JWT string.

---

.. function:: decode_jwt(token, public_key, algorithm)
   :module: app.lib.jwt_utils

   Decode and validate a JWT using the application’s public key.

   This function automatically verifies the token’s signature and standard claims (such as expiration time).

   **Parameters:**

   * **token** (*str | bytes*) – The encoded JWT string or bytes to be decoded.
   * **public_key** (*str*) – The public key used for verifying the token’s signature. Defaults to the application’s configured public key.
   * **algorithm** (*str*) – The cryptographic algorithm used for verification (e.g., [‘RS256’]). Defaults to the configured algorithm.

   **Returns:**

   * *dict* – The decoded payload as a dictionary.

   **Raises:**

   * **jwt.InvalidSignatureError** – If the token signature is invalid.
   * **jwt.ExpiredSignatureError** – If the token’s expiration time has passed.
   * **jwt.DecodeError** – If the token cannot be decoded for other reasons.
