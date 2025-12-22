CLI Guide
=========

The **IronTrack** command-line interface (CLI) is the central tool for managing the application lifecycle, from database migrations to user administration.

Main CLI Entry Point (app)
--------------------------

All core operations are performed using the ``app`` command. You can always use the ``--help`` flag at any level to see available options.

Server Management
+++++++++++++++++

Manage the FastAPI application server.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Command
     - Description
   * - ``app server dev``
     - Starts the development server with **hot-reload** enabled.
   * - ``app server run``
     - Starts the server in **production mode** (no reload, optimized).

Database Administration
+++++++++++++++++++++++

Handle schema evolution and database state.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Command
     - Description
   * - ``app database upgrade``
     - Applies all pending SQLAlchemy/Alembic migrations.
   * - ``app database --help``
     - Shows additional database tools (revision, downgrade, etc.).

User & Access Management
------------------------

These commands manage roles and user accounts. **Note:** Some commands will prompt for missing information (like passwords) interactively.

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - ``app users create-roles``
     - **Mandatory.** Initializes system roles (Superuser, Application Access, etc.) from fixtures.
   * - ``app users create-system-admin``
     - Creates a default administrator using the email defined in config.
   * - ``app users create-user``
     - Interactive command to create a new regular or superuser.
   * - - ``app users promote-to-superuser``
     - Grants superuser status and the superuser role to an existing email.

**Example: Promoting a user**

.. code-block:: bash

    app users promote-to-superuser --email user@example.com

Database Seeding
----------------

To populate the database with reference books (muscle groups, equipment, etc.) and the standard exercise collection, use the command:

.. code-block:: bash

    make seed
