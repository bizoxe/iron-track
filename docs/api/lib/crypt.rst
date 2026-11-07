Password Hashing
================

This module handles secure password management using the **Argon2id** algorithm.

.. automodule:: app.lib.crypt
   :members: get_password_hash, verify_password

---

Configuration & Performance
---------------------------

Hashing runs in a dedicated thread pool so CPU-intensive Argon2 computation never blocks the event loop.

- **Thread Pool:** :class:`~concurrent.futures.ThreadPoolExecutor` named ``Argon2Pool``.
- **Concurrency:** The pool defaults to the available CPU cores (capped at 4) and can be
  pinned via :attr:`~app.config.base.AppSettings.CRYPTO_MAX_WORKERS`.
- **Algorithm Parameters:**

    - Time Cost: |ARGON2_TIME_COST|
    - Memory Cost: |ARGON2_MEMORY_COST|
    - Parallelism: |ARGON2_PARALLELISM|
