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
