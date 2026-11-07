IronTrack
=========

.. image:: https://img.shields.io/badge/python-3.12-3776ab.svg?logo=python&logoColor=white
    :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white
    :target: https://fastapi.tiangolo.com/
.. image:: https://img.shields.io/badge/license-MIT-4bc51d.svg?logo=opensourceinitiative&logoColor=white
    :target: https://opensource.org/licenses/MIT

**IronTrack** is an experimental async backend sandbox designed for architectural exploration and performance analysis.

The project serves as a laboratory for testing concurrency patterns, database optimization, and constraint-driven experiments within a workout tracking domain.

.. note::
   **Infrastructure Context:** This project is intentionally developed and benchmarked on constrained bare-metal hardware (**AMD FX-8320 / HDD**).

   This "high-latency" environment is a deliberate architectural choice. It amplifies performance bottlenecks—such as I/O wait times and serialization overhead—that are often masked by modern cloud infrastructure. This setup forces the evaluation of concurrency patterns and optimization techniques under realistic hardware limitations.

.. warning::
   This is a learning-focused sandbox. It is not intended for production-driven business applications.

Navigation
----------

.. grid:: 1 2 2 2
    :gutter: 3

    .. grid-item-card:: 🚀 Get Started
        :link: usage/installation
        :link-type: doc

        Installation guide and environment setup.

    .. grid-item-card:: 📖 API Reference
        :link: api/index
        :link-type: doc

        Detailed technical documentation of the codebase.

.. toctree::
    :titlesonly:
    :caption: Documentation
    :hidden:

    usage/index
    api/index

.. toctree::
    :titlesonly:
    :caption: Project
    :hidden:

    contribution-guide
    changelog
