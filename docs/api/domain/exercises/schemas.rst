Exercises Schemas
=================

Shared Definitions
------------------

.. autoclass:: app.domain.exercises.schemas.ExerciseScope
   :members: SYSTEM, USER, ALL
   :undoc-members:

.. data:: app.domain.exercises.schemas.CdnRelativePath
   :annotation: = Annotated[str, Field(...)]

   Annotated ``str`` type constraining relative CDN image paths: leading ``/``,
   format ``/{exercise-directory}/{filename}.{ext}`` with a ``jpe?g``/``png``/``webp``
   extension, max 512 characters. Join rule: ``CDN_BASE_URL.rstrip('/') + path``.

Base Definitions
----------------

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseBase
   :field-show-constraints: false

Response Models
---------------

.. autoclass:: app.domain.exercises.schemas.ExerciseRead
   :undoc-members:

User Exercise Models
--------------------

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseCreate
   :field-show-constraints: false
   :inherited-members: ExerciseBase

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseUpdate
   :field-show-constraints: false
   :inherited-members: ExerciseBase

System Exercise Models
----------------------

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseCreateSystem
   :field-show-constraints: false
   :inherited-members: ExerciseBase

.. autopydantic_model:: app.domain.exercises.schemas.ExerciseUpdateSystem
   :field-show-constraints: false
   :inherited-members: ExerciseUpdate

Page Envelopes
--------------

.. autoclass:: app.domain.exercises.schemas.ExercisePage
   :undoc-members:
   :inherited-members:
