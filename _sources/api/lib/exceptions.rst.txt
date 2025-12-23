API Exceptions
==============

.. autoclass:: app.lib.exceptions.BaseAPIException
    :members:

    .. autoattribute:: status_code
       :annotation: int

    .. autoattribute:: message
       :annotation: str

    .. autoattribute:: headers
       :annotation: dict | None

---

Standard HTTP Exceptions
------------------------

.. autoclass:: app.lib.exceptions.UnauthorizedException

.. autoclass:: app.lib.exceptions.UserNotFound

.. autoclass:: app.lib.exceptions.BadRequestException

.. autoclass:: app.lib.exceptions.ConflictException

.. autoclass:: app.lib.exceptions.PermissionDeniedException

.. autoclass:: app.lib.exceptions.NotFoundException
