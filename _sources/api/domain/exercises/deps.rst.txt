Exercises Domain Dependencies
=============================

Provides dependency injection providers for exercise services, ensuring scoped database sessions for each request.

.. automodule:: app.domain.exercises.deps
   :members: provide_exercise_service

.. data:: ExerciseServiceDep
   :annotation: = Annotated[ExerciseService, Depends(provide_exercise_service)]

   Dependency injection provider for the exercise service.
