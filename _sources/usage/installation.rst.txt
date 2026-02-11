Installation
============

This guide covers setting up **IronTrack** using a hybrid approach: running the infrastructure (Database, Cache) in Docker and the application locally on your machine.

Prerequisites
-------------

Before you begin, ensure you have the following installed:

* **Docker** and **Docker Compose** (V2)
* **Git**
* **Python 3.12+** (managed via `uv <https://docs.astral.sh/uv/>`_)
* **Make**

1. Clone the Repository
-----------------------

.. code-block:: bash

    git clone https://github.com/bizoxe/iron-track.git
    cd iron-track

2. Environment Configuration
----------------------------

First, install the project dependencies and set up your local configuration files.

.. code-block:: bash

    # 1. Install dependencies and setup the project
    make install

    # 2. Copy the local development template to the config directory
    cp .env.local.template src/app/config/.env

.. tip::
   The ``.env.local.template`` is pre-configured to connect to services via ``localhost``. It uses port ``5432`` for a **direct connection** to PostgreSQL (used for simplicity of deployment in the local environment).

3. Infrastructure Setup (Docker)
--------------------------------

The application requires PostgreSQL and Valkey. Run these services in Docker to avoid manual installation.

.. code-block:: bash

    # Start infrastructure services in the background
    make infra-up

.. note::
   This command starts the essential database and cache using the configuration in ``deploy/docker-compose.infra.yaml``.

4. Initial System Setup
-----------------------

Once the infrastructure containers are running and healthy, you must initialize the database content.

.. code-block:: bash

    # 1. Deploy database migrations
    app database upgrade

    # 2. Create mandatory system roles
    app users create-roles

    # 3. (Optional) Seed the database with reference books and exercise data
    make seed

.. important::
   **Creating roles is mandatory.** You must execute ``app users create-roles`` before registering any users, as it initializes the base permission system.

5. Running the Server
---------------------

Start the FastAPI development server with hot-reload enabled:

.. code-block:: bash

    app server dev

Accessing the Application
-------------------------

Once the server is running, you can access:

* **Interactive API Documentation (Swagger):** ``http://127.0.0.1:8000/docs``

Next Steps
----------

* Explore the :doc:`cli-guide` for a full list of **available CLI commands**.
* Check the :doc:`development` guide for further technical information and advanced setups.

