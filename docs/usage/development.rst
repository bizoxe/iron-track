Development
===========

This section covers project-specific workflows and the ``Makefile`` interface.

Configuration
-------------

Initialize the project environment in the **project root**:

.. code-block:: bash

    make setup-env

This generates the necessary configuration files from templates:

* ``.env.docker``: Base infrastructure settings
* ``.env.docker.dev``: Local development overrides

.. note::
   These files are excluded from version control for security reasons. Please update the created files with your local credentials or custom settings before running ``docker compose``.

   Compose resolves ``${VAR:-default}`` placeholders in ``docker-compose.yaml`` (credentials
   of the ``postgres`` / ``pgbouncer`` services and their healthchecks) from the **shell
   environment or a root-level ``.env`` file only** — the ``env_file:`` directive injects
   variables into a service's own container and does not participate in placeholder
   substitution. The templates above list application-facing variables only; infrastructure
   credentials (``DB_USER``, ``DB_USER_PASSWORD``, ``DB_NAME``, ``PGBOUNCER_ADMIN_*``,
   ``PGBOUNCER_MONITOR_*``) fall back to the defaults baked into ``docker-compose.yaml``.

   The ``angie`` service relies on this interpolation by design: it receives its variables
   (``SERVER_NAME``, ``ALLOWED_ORIGINS_REGEX``, ``ALLOWED_ORIGINS``, ``SSL_CERT_PATH``,
   ``SSL_KEY_PATH``) via explicit ``environment:`` entries rather than ``env_file:``, so
   that application secrets (``DATABASE_URL``, ``JWT_PRIVATE_KEY``) never reach the web
   tier. Always start the stack with ``--env-file`` (see the examples below) — otherwise
   these variables resolve to empty values and the ``angie`` container exits at startup
   with an explicit configuration error. The web tier deliberately has no fallback
   defaults in ``docker-compose.yaml`` (unlike the database services): its configuration
   must always come explicitly from the environment file.

   If you customize credentials, keep them in sync with ``DATABASE_URL``: add the
   infrastructure variables to your local env file and pass it to Compose:

   .. code-block:: bash

       # Development stack (override is merged automatically):
       docker compose --env-file .env.docker.dev up -d

       # Production-like stack (base file only, override excluded):
       docker compose -f docker-compose.yaml --env-file .env.docker up -d

   .. tip::
      Alternatively, export the variables in your shell or place them in a
      project-root ``.env`` file (ignored by git) — Compose reads it automatically.

Hot-Reload & Volumes
++++++++++++++++++++

In development mode (using ``docker-compose.override.yaml``), in particular, the following local paths are mounted:

* ``src/`` → ``/workspace/app/src/`` (enables hot-reload)
* ``.env.docker.dev`` → ``/workspace/app/src/app/config/.env`` (container-specific config)

.. note::
   Changes to mounted configurations (``.env.docker.dev``) require a container restart, while code changes in ``src/`` are reflected automatically.

Startup & Migrations
--------------------

.. warning::
   The following commands automatically use your local ``docker-compose.override.yaml``.
   Ensure your configuration files are correctly initialized via ``make setup-env``
   before starting the stack.

Startup Sequence
++++++++++++++++

The initial bootstrap requires a manual role synchronization for PgBouncer:

.. code-block:: bash

    # 1. Start PostgreSQL
    docker compose --env-file .env.docker.dev up -d postgres

    # 2. Sync roles and passwords
    make pgbouncer-sync

    # 3. Start the rest of the stack
    docker compose --env-file .env.docker.dev up -d

.. warning::
   Infrastructure credentials (``DB_USER_PASSWORD``, ``PGBOUNCER_*``) are applied by the
   Postgres init script only during the **first** initialization of the ``db-data`` volume.
   Changing them later requires updating the role directly in Postgres
   (``ALTER ROLE ... WITH PASSWORD``) or recreating the environment
   (``docker compose down -v`` — note this wipes **all** project volumes:
   ``db-data``, ``cache-data`` and ``sockets``).

   After ``ALTER ROLE`` re-run ``make pgbouncer-sync``: the SCRAM verifier in
   ``pg_authid`` changes, so a previously generated ``userlist.txt`` becomes stale.
   The script re-reads the verifiers and reloads PgBouncer via SIGHUP automatically.

Database Migrations
+++++++++++++++++++

To apply migrations manually:

.. code-block:: bash

    docker compose run --rm migrator

Networking & IPC
----------------

The stack uses **Unix Domain Sockets (UDS)** for inter-container communication between **Angie** and **Granian**.

* **Socket Path**: Shared via a Docker volume at ``/run/app/granian.sock``.
* **Permissions**: Granian is configured with ``--uds-permissions 438`` (octal ``666``) to allow Angie to read/write to the socket.
* **Healthchecks**: The application health is verified by a Python script performing a raw HTTP/1.1 request directly over the Unix socket.

.. note::
   In the production stack, the API does not listen on a TCP port (e.g., 8000). All requests must be routed through the Angie proxy.

Production Tuning
-----------------

Host System Configuration
+++++++++++++++++++++++++

For optimal **HTTP/3 (QUIC)** performance, you must increase the UDP receive and send buffer sizes on the **host machine**.

**1. Create a dedicated configuration file**
    To maintain a clean system, avoid modifying the main ``sysctl.conf``.
    Create a separate file for Angie:

    .. code-block:: bash

        sudo nano /etc/sysctl.d/99-angie-quic.conf

**2. Add network buffer parameters**
    Paste the following lines into the file:

    .. code-block:: text

        net.core.rmem_max=2500000
        net.core.wmem_max=2500000

**3. Apply changes**
    Load the new configuration immediately without a reboot:

    .. code-block:: bash

        sudo sysctl --system

SSL & Certificates
------------------

Development (Local HTTPS)
+++++++++++++++++++++++++

Use ``mkcert`` to create a locally-trusted development certificate.

**1. Install local CA (once per machine)**

.. code-block:: bash

    mkcert -install

**2. Generate certificates**

.. code-block:: bash

    mkdir -p deploy/certs
    mkcert -cert-file deploy/certs/local-cert.pem \
           -key-file deploy/certs/local-key.pem \
           app.localhost localhost 127.0.0.1 ::1

Production
++++++++++

Use **Certbot** on the host. Since Angie mounts ``deploy/certs`` as read-only (``:ro``), reload the service after certificate renewal:

.. code-block:: bash

    docker exec angie_iron_track angie -s reload

Makefile Reference
------------------

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Command
     - Description
   * - ``make install``
     - Resets the environment and installs fresh dependencies.
   * - ``make pgbouncer-sync``
     - Syncs Postgres roles to PgBouncer ``userlist.txt``.
   * - ``make upgrade``
     - Updates ``uv.lock`` and pre-commit hooks.
   * - ``make lint`` / ``make test``
     - Standard quality assurance commands.
   * - ``make release``
     - Bumps the version in ``pyproject.toml`` and ``src/app/__about__.py`` and syncs ``uv.lock`` (``make release bump=patch|minor|major``). No commit or tag is created — commit the result and push a ``vX.Y.Z`` tag manually to trigger the release workflow.

.. dropdown:: View Full Makefile

    .. literalinclude:: ../../Makefile
        :language: make
