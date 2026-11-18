Catalogs Schemas
================

Base Definitions
----------------

.. autoclass:: app.domain.catalogs.schemas.CatalogReadBase
   :undoc-members:

.. autopydantic_model:: app.domain.catalogs.schemas.CatalogCreateBase
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false

.. autopydantic_model:: app.domain.catalogs.schemas.CatalogUpdateBase
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogCreateBase

.. autopydantic_model:: app.domain.catalogs.schemas.CatalogRestoreBase
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogCreateBase

Response Models
---------------

.. autoclass:: app.domain.catalogs.schemas.EquipmentRead
   :undoc-members:
   :inherited-members:

.. autoclass:: app.domain.catalogs.schemas.MuscleGroupRead
   :undoc-members:
   :inherited-members:

.. autoclass:: app.domain.catalogs.schemas.TagRead
   :undoc-members:
   :inherited-members:

Input Models
------------

.. autopydantic_model:: app.domain.catalogs.schemas.EquipmentCreate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogCreateBase

.. autopydantic_model:: app.domain.catalogs.schemas.EquipmentUpdate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogUpdateBase

.. autopydantic_model:: app.domain.catalogs.schemas.EquipmentRestore
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogRestoreBase

.. autopydantic_model:: app.domain.catalogs.schemas.MuscleGroupCreate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogCreateBase

.. autopydantic_model:: app.domain.catalogs.schemas.MuscleGroupUpdate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogUpdateBase

.. autopydantic_model:: app.domain.catalogs.schemas.MuscleGroupRestore
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogRestoreBase

.. autopydantic_model:: app.domain.catalogs.schemas.TagCreate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogCreateBase

.. autopydantic_model:: app.domain.catalogs.schemas.TagUpdate
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogUpdateBase

.. autopydantic_model:: app.domain.catalogs.schemas.TagRestore
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :inherited-members: CatalogRestoreBase

List Envelopes
--------------

.. autoclass:: app.domain.catalogs.schemas.CatalogList
   :undoc-members:

.. autoclass:: app.domain.catalogs.schemas.EquipmentList
   :undoc-members:
   :inherited-members:

.. autoclass:: app.domain.catalogs.schemas.MuscleGroupList
   :undoc-members:
   :inherited-members:

.. autoclass:: app.domain.catalogs.schemas.TagList
   :undoc-members:
   :inherited-members:
