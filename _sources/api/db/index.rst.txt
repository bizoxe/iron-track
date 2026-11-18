Database Layer
==============

SQLAlchemy models for the application's persistent data, plus the shared database machinery around them:
model bases and mixins, PostgreSQL bindings for the domain enums, and global soft-delete filtering.

.. toctree::
   :maxdepth: 1
   :caption: Models

   catalog
   exercise
   role
   user

.. toctree::
   :maxdepth: 1
   :caption: Shared Building Blocks

   base
   enums
   mixins
   soft_delete
