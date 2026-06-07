Catalogs Domain Schemas
=======================

Pydantic & msgspec.Struct Data Transfer Objects (DTOs) for the Catalogs sub-domain.

Base Definitions
----------------

.. autoclass:: app.domain.catalogs.schemas.FieldsReadBase
   :undoc-members:

.. autopydantic_model:: app.domain.catalogs.schemas.FieldsCreateBase
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false

.. autopydantic_model:: app.domain.catalogs.schemas.FieldsUpdateBase
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: FieldsCreateBase

---

Muscle Group Models
-------------------

.. autoclass:: app.domain.catalogs.schemas.MuscleGroupRead
   :undoc-members:
   :inherited-members:

.. autopydantic_model:: app.domain.catalogs.schemas.MuscleGroupCreate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: FieldsCreateBase

.. autopydantic_model:: app.domain.catalogs.schemas.MuscleGroupUpdate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: FieldsUpdateBase

---

Equipment Models
----------------

.. autoclass:: app.domain.catalogs.schemas.EquipmentRead
   :undoc-members:
   :inherited-members:

.. autopydantic_model:: app.domain.catalogs.schemas.EquipmentCreate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: FieldsCreateBase

.. autopydantic_model:: app.domain.catalogs.schemas.EquipmentUpdate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: FieldsUpdateBase

---

Exercise Tag Models
-------------------

.. autoclass:: app.domain.catalogs.schemas.ExerciseTagRead
   :undoc-members:
   :inherited-members:

.. autopydantic_model:: app.domain.catalogs.schemas.ExerciseTagCreate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: FieldsCreateBase

.. autopydantic_model:: app.domain.catalogs.schemas.ExerciseTagUpdate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: FieldsUpdateBase
