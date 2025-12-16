Base Settings Models
====================

.. automodule:: app.config.base
    :no-members:
    :no-inherited-members:

Defines all application settings models (dataclasses) and the central function for loading configuration.

---

Configuration Loader
--------------------

.. autofunction:: app.config.base.get_settings
   :noindex:

---

Settings Container (`Settings`)
-------------------------------

.. autoclass:: app.config.base.Settings
    :members:
    :exclude-members: from_env, __post_init__

---

Application Settings (`AppSettings`)
------------------------------------

.. autoclass:: app.config.base.AppSettings
    :members:
    :exclude-members:

---

Logger Settings (`LogSettings`)
-------------------------------

.. autoclass:: app.config.base.LogSettings
    :members:
    :exclude-members: _settings

---

Database Settings (`DatabaseSettings`)
--------------------------------------

.. autoclass:: app.config.base.DatabaseSettings
    :members:
    :exclude-members: _engine_instance, get_engine, configure_standard_engine, configure_pgbouncer_engine

---

JWT Settings (`JWTSettings`)
----------------------------

.. autoclass:: app.config.base.JWTSettings
    :members:
    :exclude-members: auth_jwt_private_key, auth_jwt_public_key

---

Redis Settings (`RedisSettings`)
--------------------------------

.. autoclass:: app.config.base.RedisSettings
    :members:
    :exclude-members: get_client
