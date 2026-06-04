Exercises Domain Services
=========================

Domain services encapsulating the business logic for exercise models, including complex relationship management and custom filtering.

---

Exercise Service (`ExerciseService`)
------------------------------------

.. autoclass:: app.domain.exercises.services.ExerciseService()
   :no-inherited-members:
   :members: get_exercise_by_filter, update_exercise, delete_exercise, get_exercises_paginated_dto
   :exclude-members: ExerciseRepository, repository_type, _rel_keys, muscles, equipment, tags, to_model_on_create, to_model_on_update, to_model_on_upsert, _validate_and_populate_fields, _raise_muscle_not_found, _validate_ids, _populate_model
