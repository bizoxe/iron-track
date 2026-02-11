Base Models & Structures
========================

This module provides foundation classes for data representation, ensuring consistent
**camelCase** naming for frontend integration across both **msgspec** and **Pydantic**.

Msgspec Structures
------------------
High-performance structures for efficient serialization.

.. autoclass:: app.lib.schema.BaseStruct

.. autoclass:: app.lib.schema.CamelizedBaseStruct

Pydantic Schemas
----------------
Validation-ready schemas for request parsing and complex data logic.

.. autopydantic_model:: app.lib.schema.CamelizedBaseSchema



