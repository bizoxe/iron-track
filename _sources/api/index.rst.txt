API Reference
=============

Code reference structured by architectural layer.

Configuration
-------------

Settings models, environment loading, SQLAlchemy wiring, and application constants.

.. toctree::
   :maxdepth: 2

   config/index

Infrastructure
--------------

Application bootstrap and runtime: server setup, database layer, shared components, and operational scripts.

.. toctree::
   :maxdepth: 2

   server/index
   db/index
   lib/index
   scripts/index

Domain Modules
--------------

Business logic organized by functional sub-domains.

.. toctree::
   :maxdepth: 2

   domain/index

Application Entry
-----------------

The composition root: the FastAPI application instance and the CLI entry point.

.. toctree::
   :maxdepth: 1

   main
