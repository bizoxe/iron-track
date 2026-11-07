Catalogs Filters
================

Base Catalog Filters
--------------------

.. autopydantic_model:: app.domain.catalogs.filters.CatalogFilters
   :field-show-constraints: false
   :exclude-members: model_post_init, as_aa_filters

.. autoproperty:: app.domain.catalogs.filters.CatalogFilters.as_aa_filters

Catalog Filters with Retired Items
----------------------------------

.. autopydantic_model:: app.domain.catalogs.filters.CatalogFiltersWithRetired
   :field-show-constraints: false
   :inherited-members: CatalogFilters

.. autoproperty:: app.domain.catalogs.filters.CatalogFiltersWithRetired.as_aa_filters
