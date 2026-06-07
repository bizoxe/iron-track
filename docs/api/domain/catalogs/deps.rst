Catalogs Domain Dependencies
============================

Provides dependency injection providers for catalog services, ensuring scoped database sessions for each request.

.. automodule:: app.domain.catalogs.deps
   :members: provide_muscle_group_service, provide_equipment_service, provide_exercise_tag_service

.. data:: MuscleGroupDep
   :annotation: = Annotated[MuscleGroupService, Depends(provide_muscle_group_service)]

   Dependency injection provider for the muscle group service.

.. data:: EquipmentDep
   :annotation: = Annotated[EquipmentService, Depends(provide_equipment_service)]

   Dependency injection provider for the equipment service.

.. data:: ExerciseTagDep
   :annotation: = Annotated[ExerciseTagService, Depends(provide_exercise_tag_service)]

   Dependency injection provider for the exercise tag service.
