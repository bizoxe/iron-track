Catalogs Domain Services
========================

Domain services encapsulating the business logic and caching strategies for catalog models.

---

Base Catalog Service (`BaseCatalogService`)
-------------------------------------------

.. autoclass:: app.domain.catalogs.services.BaseCatalogService()
   :no-inherited-members:
   :undoc-members:
   :members: read_schema, get_list_items, get_all_cached, get_managed_objs, upsert_many, create, update, delete
   :exclude-members: _invalidate_cache

---

Muscle Group Service (`MuscleGroupService`)
-------------------------------------------

.. autoclass:: app.domain.catalogs.services.MuscleGroupService()
   :no-inherited-members:
   :undoc-members:
   :members: read_schema
   :exclude-members: MuscleGroupRepository, repository_type

---

Equipment Service (`EquipmentService`)
--------------------------------------

.. autoclass:: app.domain.catalogs.services.EquipmentService()
   :no-inherited-members:
   :undoc-members:
   :members: read_schema
   :exclude-members: EquipmentRepository, repository_type

---

Exercise Tag Service (`ExerciseTagService`)
-------------------------------------------

.. autoclass:: app.domain.catalogs.services.ExerciseTagService()
   :no-inherited-members:
   :undoc-members:
   :members: read_schema
   :exclude-members: ExerciseTagRepository, repository_type
