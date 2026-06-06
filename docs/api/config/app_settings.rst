SQLAlchemy and Dependency Configuration
=======================================

Configures SQLAlchemy, Alembic, and the database session dependency injection.

.. autodata:: app.config.app_settings.alchemy
   :noindex:
   :no-value:

.. autodata:: app.config.app_settings.sqlalchemy_config
   :noindex:
   :no-value:

.. data:: app.config.app_settings.DatabaseSession
   :annotation: = Annotated[AsyncSession, Depends(alchemy.provide_session())]

   FastAPI dependency for providing and managing the async database session lifecycle.
