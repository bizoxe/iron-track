Reference Data Models
=====================

Core reference data entities for exercise categorization (muscle groups, equipment, and metadata tags).

Association Tables
------------------

.. automodule:: app.db.models.reference
   :members: exercise_primary_muscles, exercise_secondary_muscles, exercise_equipment, exercise_tag_map
   :exclude-members: MuscleGroup, Equipment, ExerciseTag
   :no-value:

Entities
--------

.. autoclass:: MuscleGroup
   :members:
   :exclude-members: id
   :undoc-members:

.. autoclass:: Equipment
   :members:
   :exclude-members: id
   :undoc-members:

.. autoclass:: ExerciseTag
   :members:
   :undoc-members:
   :exclude-members: id
