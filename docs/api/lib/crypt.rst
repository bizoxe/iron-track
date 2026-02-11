Security Utilities
==================

This module handles secure password management using the **Argon2id** algorithm.

.. important::
   Password hashing is a CPU-bound operation. To prevent blocking the FastAPI
   asynchronous event loop, all hashing and verification operations are executed
   within a dedicated thread pool.

.. automodule:: app.lib.crypt
