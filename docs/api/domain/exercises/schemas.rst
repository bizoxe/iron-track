Exercises Domain Schemas
========================

Pydantic & msgspec.Struct Data Transfer Objects (DTOs) for the Exercises sub-domain.

---

Utility Definitions
-------------------

.. autoclass:: app.domain.exercises.schemas.ExerciseScope
    :members: SYSTEM, USER, ALL
    :undoc-members:

.. autoclass:: app.domain.exercises.schemas.DifficultyLevelType
    :members: BEGINNER, INTERMEDIATE, EXPERT
    :undoc-members:

.. autoclass:: app.domain.exercises.schemas.ForceType
    :members: PULL, PUSH, STATIC
    :undoc-members:

.. autoclass:: app.domain.exercises.schemas.MechanicType
    :members: COMPOUND, ISOLATION
    :undoc-members:

.. autoclass:: app.domain.exercises.schemas.CategoryType
    :members: STRENGTH, STRETCHING, PLYOMETRICS, STRONGMAN, POWERLIFTING, CARDIO, OLYMPIC_WEIGHTLIFTING
    :undoc-members:

Base Definitions
----------------

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseBase
   :field-show-constraints: false

---

User Exercise Models
--------------------

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseCreate
   :field-show-constraints: false
   :inherited-members: ExerciseBase

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseUpdate
   :field-show-constraints: false
   :inherited-members: ExerciseBase

---

System Exercise Models
----------------------

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseCreateSystem
   :field-show-constraints: false
   :inherited-members: ExerciseCreate

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseUpdateSystem
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: ExerciseUpdate

---

Response Models
---------------

.. autoclass:: app.domain.exercises.schemas.ExerciseRead
   :undoc-members:
