Security Utilities
==================

This module handles secure password management using the **Argon2id** algorithm.

.. automodule:: app.lib.crypt
   :members: get_password_hash, verify_password
   :exclude-members: crypto_executor, hasher

Configuration & Performance
---------------------------
The security module is automatically tuned based on available CPU resources to balance high security with system responsiveness.

- **Thread Pool:** Uses a :class:`~concurrent.futures.ThreadPoolExecutor` named "Argon2Pool" to prevent CPU-intensive hashing from blocking the FastAPI event loop.
- **Concurrency:** Scales dynamically (up to 4 parallel workers) to ensure optimal hashing throughput without resource contention.
- **Algorithm:**
    - Time Cost: |ARGON2_TIME_COST|
    - Memory Cost: |ARGON2_MEMORY_COST|
    - Parallelism: |ARGON2_PARALLELISM|
