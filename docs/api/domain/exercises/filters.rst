Exercises Domain Filters
========================

Provides filter schemas for exercise resources, enabling advanced scope management, categorization, and caching strategies.

.. autopydantic_model:: app.domain.exercises.filters.ExerciseFilters
   :field-show-constraints: false
   :inherited-members: CommonFilters
   :exclude-members: build_exercise_filters

Technical Methods
-----------------
.. automethod:: app.domain.exercises.filters.ExerciseFilters.build_exercise_filters

