Accounts Filters
================

User Filters
------------

.. autopydantic_model:: app.domain.accounts.filters.UserFilters
   :field-show-constraints: false
   :inherited-members: CommonFilters
   :exclude-members: range_field_name, range_filter

.. autoproperty:: app.domain.accounts.filters.UserFilters.as_aa_filters

User Exercise Filters
---------------------

.. autopydantic_model:: app.domain.accounts.filters.UserExerciseFilters
   :field-show-constraints: false
   :inherited-members: CommonFilters
   :exclude-members: range_field_name, range_filter, build_user_exercise_filters

.. automethod:: app.domain.accounts.filters.UserExerciseFilters.build_user_exercise_filters
