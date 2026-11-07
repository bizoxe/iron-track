Base Settings Models
====================

Defines all application settings models (dataclasses) and the central function for loading configuration.

.. automodule:: app.config.base
    :no-members:
    :no-inherited-members:

Configuration Loader
--------------------

.. autofunction:: app.config.base.get_settings
   :noindex:

Settings Container
------------------

.. autoclass:: app.config.base.Settings
    :members:
    :exclude-members: from_env

---

Application Settings
--------------------

.. autoclass:: app.config.base.AppSettings
    :members:

Logger Settings
---------------

.. autoclass:: app.config.base.LogSettings
    :members:

Database Settings
-----------------

.. autoclass:: app.config.base.DatabaseSettings
    :members:

JWT Settings
------------

.. autoclass:: app.config.base.JWTSettings
    :members:

Cache Settings
--------------

.. autoclass:: app.config.base.CacheSettings
    :members:
