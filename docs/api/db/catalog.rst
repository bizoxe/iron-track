Catalog Models
==============

Reference entities for exercise categorization (muscle groups, equipment, and tags),
plus the association objects and tables linking them to exercises.

Association Object
-------------------

.. autoclass:: app.db.models.catalog.ExerciseMuscle
   :members:
   :undoc-members:

Association Tables
------------------

.. automodule:: app.db.models.catalog
   :members: exercise_equipment, exercise_tag
   :exclude-members: ExerciseMuscle, CatalogBase, MuscleGroup, Equipment, Tag
   :no-value:

Base Model
----------

.. autoclass:: app.db.models.catalog.CatalogBase
   :members:
   :exclude-members: id, deleted_at

Entities
--------

.. autoclass:: app.db.models.catalog.MuscleGroup
   :members:
   :undoc-members:
   :exclude-members: id, deleted_at

.. autoclass:: app.db.models.catalog.Equipment
   :members:
   :undoc-members:
   :exclude-members: id, deleted_at

.. autoclass:: app.db.models.catalog.Tag
   :members:
   :undoc-members:
   :exclude-members: id, deleted_at
