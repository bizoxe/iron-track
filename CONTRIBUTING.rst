Contribution Guide
==================

Setting up the environment
--------------------------

The easiest way to set up the development environment is to use the provided ``Makefile``.
This project requires `Astral's uv <https://docs.astral.sh/uv/>`_ for dependency management.

1. If you do not have ``uv`` installed, run: ``make install-uv``
2. Run the full installation command:

   .. code-block:: console

      make install

   This command **re-creates the environment** (an existing ``.venv`` is removed along with build artifacts), installs the project in **editable mode**, and sets up all development dependencies.

3. Install `pre-commit <https://pre-commit.com/>`_ hooks:

   .. code-block:: console

      uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

   This registers both hook stages locally: ``pre-commit`` (linters on staged files)
   and ``commit-msg`` (Conventional Commit format validation).

.. tip::
   For detailed setup instructions and development workflows,
   see the `Installation Guide <https://bizoxe.github.io/iron-track/usage/installation.html>`_
   and the `Development Workflow <https://bizoxe.github.io/iron-track/usage/development.html>`_.

Code contributions
------------------

Workflow
++++++++

1. `Fork <https://github.com/bizoxe/iron-track/fork>`_ the `repository <https://github.com/bizoxe/iron-track>`_.
2. Clone your fork locally with git.
3. Run ``make install`` (see `Setting up the environment`_).
4. Create a branch for your changes.
5. Make your changes and ensure they follow the project style.
6. (Optional) Run ``make lint`` or ``uv run pre-commit run --all-files`` manually to apply fixes and check types before committing.
7. Commit your changes to git.
8. Push the changes to your fork.
9. Open a `Pull Request <https://github.com/bizoxe/iron-track/pulls>`_.

   .. important::
      Give the pull request a descriptive title indicating what it changes.
      If it fixes an open issue, include the issue number.
      For example: ``fix: update user profile validation logic (#123)``.

.. tip::
   All commits and pull requests must follow the `Conventional Commit format <https://www.conventionalcommits.org>`_ —
   commit messages are parsed by ``git-cliff`` to generate the public changelog.
   Before pushing, ensure all tests pass by running ``make test``.

.. note::
   Every pull request is automatically verified by CI: **pre-commit** checks, the **pytest**
   suite with coverage, and **CodeQL** analysis. Changes to the documentation or application
   sources additionally trigger a strict Sphinx build.

Running the tests
-----------------

The test suite requires **Docker**: the ``pytest-databases`` fixtures automatically spin up
dedicated PostgreSQL and Valkey containers. No additional environment setup is needed —
the committed ``.env.testing`` provides the required configuration, including a test-only
JWT key.

.. code-block:: console

   make test        # Run the suite in parallel (2 workers)
   make coverage    # Run tests and generate HTML/XML coverage reports

Project documentation
---------------------

The documentation is located in the ``/docs`` directory and is built with `ReST <https://docutils.sourceforge.io/rst.html>`_ and `Sphinx <https://www.sphinx-doc.org/en/master/>`_.

If you are unfamiliar with these tools, read the `ReStructuredText primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_ and the `Sphinx quickstart <https://www.sphinx-doc.org/en/master/usage/quickstart.html>`_.

Docs theme
++++++++++

The project uses the `Shibuya <https://shibuya.lepture.com/>`_ theme to maintain a modern and clean look. If you wish to contribute to the docs style or static site generation, please consult the theme documentation.

Running the docs locally
++++++++++++++++++++++++

To work on the documentation with live-reload (recommended):

.. code-block:: console

     make docs-serve

The documentation will be available at ``http://localhost:8002``.

Alternatively, you can build them with:

.. code-block:: console

     make docs

Community standards
-------------------

* This project follows the `Code of Conduct <https://github.com/bizoxe/iron-track/blob/main/.github/CODE_OF_CONDUCT.md>`_. By participating, you are expected to uphold it.
* Please do not report security vulnerabilities through public GitHub issues — see the `Security Policy <https://github.com/bizoxe/iron-track/blob/main/.github/SECURITY.md>`_ and contact the maintainer directly.

By contributing to IronTrack, you agree that your contributions will be licensed under the `MIT License <https://github.com/bizoxe/iron-track/blob/main/LICENSE>`_.

