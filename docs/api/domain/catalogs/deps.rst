Catalogs Dependencies
=====================

.. automodule:: app.domain.catalogs.deps
   :members: provide_muscle_groups_service, provide_equipment_service, provide_tags_service

.. data:: MuscleGroupDep
   :annotation: = Annotated[MuscleGroupService, Depends(provide_muscle_groups_service)]

   Injectable ``MuscleGroupService`` scoped to the request.

.. data:: EquipmentDep
   :annotation: = Annotated[EquipmentService, Depends(provide_equipment_service)]

   Injectable ``EquipmentService`` scoped to the request.

.. data:: TagDep
   :annotation: = Annotated[TagService, Depends(provide_tags_service)]

   Injectable ``TagService`` scoped to the request.
