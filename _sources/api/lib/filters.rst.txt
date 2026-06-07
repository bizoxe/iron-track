Query Filters
=============

This module provides standardized logic for pagination, sorting, and keyword search,
bridging frontend request parameters with **Advanced Alchemy** statement filters.

Common Request Filters
----------------------

.. autopydantic_model:: app.lib.filters.CommonFilters
   :field-show-constraints: false
   :exclude-members: aa_technical_filters, model_post_init
