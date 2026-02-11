Custom Regex Errors
===================

.. autoclass:: app.lib.pretty_regex_error_msgs.RegexValidator
    :special-members: __init_subclass__
    :undoc-members:

    .. admonition:: Usage Example
       :class: tip

       To create a new validator, subclass ``RegexValidator``:

       .. code-block:: python

          import re

          class PasswordValidator(
              RegexValidator,
              pattern=re.compile(r"^(?=.*[A-Z]).{8,}$"),
              error_message="Password must be at least 8 chars with 1 uppercase"
          ):
              """Validator for user passwords."""
