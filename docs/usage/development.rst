Development
===========

This section covers project-specific workflows and the ``Makefile`` interface.

Configuration
-------------

Initialize the application environment file:

.. code-block:: bash

    cp .env.docker.template .env.docker

Hot-Reload & Volumes
++++++++++++++++++++

In development mode (using ``docker-compose.override.yaml``), the following local paths are mounted:

* ``src/`` → ``/workspace/app/src/`` (enables hot-reload)
* ``.env.docker`` → ``/workspace/app/src/app/config/.env`` (container-specific config)

Startup Sequence
----------------

The initial bootstrap requires a manual role synchronization for PgBouncer:

.. code-block:: bash

    # 1. Start PostgreSQL
    docker compose up -d postgres

    # 2. Sync roles and passwords
    make pgbouncer-sync

    # 3. Start the rest of the stack
    docker compose up -d

Database Migrations
-------------------

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
   The API does not listen on a TCP port (e.g., 8000). All requests must be routed through the Angie proxy.

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

.. dropdown:: View Full Makefile

    .. literalinclude:: ../../Makefile
        :language: make

