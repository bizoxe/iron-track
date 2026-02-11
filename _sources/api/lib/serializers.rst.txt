Serialization Registry
======================

This module provides a centralized registry for high-performance serialization logic.
It defines how domain models are encoded and decoded when interacting with external
systems like distributed caches, message brokers, or database drivers.

MsgSpec Integration
-------------------
Core components utilizing **msgpack** for compact binary representation.

.. autoclass:: app.lib.serializers.MsgSpecRegistry
   :private-members: _ENCODER

Registration Logic
------------------

.. autofunction:: app.lib.serializers.cashews_registry
