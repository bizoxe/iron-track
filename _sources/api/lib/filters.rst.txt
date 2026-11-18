Query Filters
=============

.. autofunction:: app.lib.filters.camel_to_snake

---

Common Request Filters
----------------------

.. autopydantic_model:: app.lib.filters.CommonFilters
   :field-show-constraints: false
   :exclude-members: search_fields, model_post_init, as_aa_filters

.. autoproperty:: app.lib.filters.CommonFilters.as_aa_filters

Created-At Range Filters
------------------------

.. autopydantic_model:: app.lib.filters.CreatedAtRangeFilters
   :field-show-constraints: false
   :exclude-members: range_field_name, range_filter, build_user_exercise_filters

.. autoproperty:: app.lib.filters.CreatedAtRangeFilters.range_filter
