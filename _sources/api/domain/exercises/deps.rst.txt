Exercises Dependencies
======================

.. automodule:: app.domain.exercises.deps
   :members:

.. data:: ExerciseServiceDep
   :annotation: = Annotated[ExerciseService, Depends(provide_exercises_service)]

   Injectable ``ExerciseService`` scoped to the request.
