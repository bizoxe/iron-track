Changelog
=========

All notable changes to this project will be documented in this file.

[Unreleased]
------------


⚙️ Miscellaneous Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`ef5dceb <https://github.com/bizoxe/iron-track/commit/ef5dcebeabadf7407051e373d580593b5137797e>`_) - Include tests in mypy checks and bump ruff-pre-commit (alexander)

* (`a4aea16 <https://github.com/bizoxe/iron-track/commit/a4aea16c921dc41cf6690e2509ada4652fb0ba2d>`_) - Cosmetic code fixes and documentation polish (alexander)


🎨 Styling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`7516069 <https://github.com/bizoxe/iron-track/commit/7516069665f0584fa1b47a48b0a4b9b3aa93f703>`_) (**alembic**) - Wrap long line in env.py (alexander)


🐛 Bug Fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`9d63dff <https://github.com/bizoxe/iron-track/commit/9d63dffe6b0dfaa8db92268fb50430cd0b06fec9>`_) (**filters**) - Scope query-param constraints to the non-null branch (alexander)

* (`ffc5fd4 <https://github.com/bizoxe/iron-track/commit/ffc5fd4307f72d1de76266866bc8a5eb4303574b>`_) (**accounts**) - Return banned accounts from the banned slice (alexander)

* (`69f4b81 <https://github.com/bizoxe/iron-track/commit/69f4b81c38a85295c8d80972669817cc23733954>`_) (**lib**) - Prevent search cache key collisions in filters.py (alexander)

* (`a2f1d7f <https://github.com/bizoxe/iron-track/commit/a2f1d7fc39195e18ddd4033d9dfbb64422ae63e6>`_) (**accounts**) - Harden JWT validation (alexander)

* (`3cc3616 <https://github.com/bizoxe/iron-track/commit/3cc3616ec400aac1efe44e3196f6ab78db78c76a>`_) (**system**) - Report health check failures without crashing (alexander)

* (`c1bf81a <https://github.com/bizoxe/iron-track/commit/c1bf81ac87362f758010b0552c2a22a5d8210ccb>`_) (**observability**) - Lost json tracebacks and duplicate listener (alexander)

* (`c79ee3c <https://github.com/bizoxe/iron-track/commit/c79ee3c7a1f8ed55c18a19426adb60f1e5406218>`_) (**main**) - Handle ClickException for clean error output (alexander)


👷 CI/CD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`ddd114a <https://github.com/bizoxe/iron-track/commit/ddd114aba28f59522a9c286e9ec6e2e61b5c2666>`_) - Harden github actions workflows (alexander)

* (`a267fec <https://github.com/bizoxe/iron-track/commit/a267fec1468b1cc79c8d4aa43e6a992e210b2876>`_) - Remove unused JWT env from tests and drop release prerelease flag (alexander)

* (`02077ba <https://github.com/bizoxe/iron-track/commit/02077ba09e14a44f36719880a3fbe8ef518b180a>`_) (**docs**) - Setup automated changelog generation (alexander)


📚 Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`6fbdc58 <https://github.com/bizoxe/iron-track/commit/6fbdc5833917d1896de8ea583104361b8e138eb4>`_) - Explain env policy and pgbouncer resync (alexander)

* (`02fb940 <https://github.com/bizoxe/iron-track/commit/02fb94028956244356c6c1eb416f4f7646aef7c0>`_) - Redesign schema blueprint and add deletion policy ADR (alexander)

* (`cef87c1 <https://github.com/bizoxe/iron-track/commit/cef87c149037c6afb1f28f2af0feff0701f75500>`_) (**benchmarks**) - Fix links and pin code revision (alexander)

* (`690c076 <https://github.com/bizoxe/iron-track/commit/690c0761bd69601bb4bd7a072fc75f1a2a639d84>`_) (**api**) - Regenerate reference for current code (alexander)

* (`262f262 <https://github.com/bizoxe/iron-track/commit/262f2628cc7d229e5ad02de766459fcaa6beb6d4>`_) - Rework usage guides, landing page, config (alexander)

* (`2366f76 <https://github.com/bizoxe/iron-track/commit/2366f7646599e78a46a7c42013aea55231ec7ae2>`_) (**contributing**) - Update contribution guide (alexander)

* (`713af1f <https://github.com/bizoxe/iron-track/commit/713af1f707b37d5faac556316142a4c9a735a3ce>`_) - Update changelog [skip ci] (github-actions[bot])


📦 Build System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`fd10eb9 <https://github.com/bizoxe/iron-track/commit/fd10eb9de570c680f97b4b49a63afe5da1ef005b>`_) - Rework deploy stack and docker tooling (alexander)

* (`6ad398e <https://github.com/bizoxe/iron-track/commit/6ad398e8e86b531ce55d75ea5cf1c7557263b485>`_) - Pin python to 3.12 and exclude .env from distributions (alexander)

* (`ea04972 <https://github.com/bizoxe/iron-track/commit/ea049723645a099adc491401fbafe251f4c66086>`_) - Refresh deps, tooling, and env templates (alexander)

* (`94e2b02 <https://github.com/bizoxe/iron-track/commit/94e2b0288cd625fc219713cc6982c88729fc31b0>`_) (**pgbouncer**) - Bump PgBouncer to 1.25.2 (alpine 3.24) (alexander)

* (`692de4a <https://github.com/bizoxe/iron-track/commit/692de4a95de7efd4805c7d0290ab0d6f77068251>`_) (**git-cliff**) - Enhance changelog template and commit parsers (alexander)

* (`5c8ccac <https://github.com/bizoxe/iron-track/commit/5c8ccac4703f3b0adbd5e82081577124df76fa13>`_) (**deps**) - Bump github/codeql-action from 4 to 4.37.4 (#16) [skip ci] (dependabot[bot])

* (`9a73b6b <https://github.com/bizoxe/iron-track/commit/9a73b6b1a5aa17f5f43fe8941f090dfea0d0cde2>`_) (**deps**) - Bump JamesIves/github-pages-deploy-action (#17) [skip ci] (dependabot[bot])

* (`366c560 <https://github.com/bizoxe/iron-track/commit/366c560cff1caad24db776c58ad29e20794b8d19>`_) (**deps**) - Bump actions/checkout from 6 to 7 [skip ci] (dependabot[bot])


🛠️ Refactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`00d147e <https://github.com/bizoxe/iron-track/commit/00d147e6624188f9d4c9b1adfaca1fe261d02e59>`_) (**lib**) - Remove unused auto_error flag in JWTCookieSecurity (alexander)

* (`ff81308 <https://github.com/bizoxe/iron-track/commit/ff81308d011bc6afadd065cf974c6c5a47b84f39>`_) (**lib**) - Rework error responses and reorder exceptions (alexander)

* (`566c006 <https://github.com/bizoxe/iron-track/commit/566c006fad8c7a6706526bf26c9b0d5a03392577>`_) (**serialization**) - Replace pickle cache with msgspec envelopes (alexander)

* (`11d7d49 <https://github.com/bizoxe/iron-track/commit/11d7d490820a0c10b1b475b24e375e016d9f23a5>`_) (**config**) - Tighten settings structure and docstrings (alexander)

* (`15556de <https://github.com/bizoxe/iron-track/commit/15556de4f77993c5fc76cec10c87595fd13e7a14>`_) (**exercises**) - Rework muscle junction and refine system schemas (alexander)

* (`82b43f8 <https://github.com/bizoxe/iron-track/commit/82b43f847ec4c470048a574aa9e2365e21fddd72>`_) (**catalogs**) - Migrate to soft delete with restore and Tag rename (alexander)

* (`9144a1e <https://github.com/bizoxe/iron-track/commit/9144a1e147a165780c152e88824e64b91389c068>`_) (**scripts**) - Restructure user CLI commands and seeder (alexander)

* (`fef161d <https://github.com/bizoxe/iron-track/commit/fef161d0972aecc0738af7fd69b533eeffb34c65>`_) (**fixtures**) - Rework exercise fixtures and role descriptions (alexander)

* (`281080f <https://github.com/bizoxe/iron-track/commit/281080f8af628fdebfe5e20e856d86e976154a78>`_) (**migrations**) - Rebase history for singular tables and soft delete (alexander)

* (`35b1f76 <https://github.com/bizoxe/iron-track/commit/35b1f762b7651f9195e4c068a8c789aef14b3258>`_) (**db**) - Introduce soft delete and singular table names (alexander)

* (`98a9af5 <https://github.com/bizoxe/iron-track/commit/98a9af5653fa63a3f5663e3e1dc356faf53005b5>`_) (**domain**) - Extract shared enums into enums.py (alexander)

* (`658b8cc <https://github.com/bizoxe/iron-track/commit/658b8cc0736bf4cd4be5a0a51e0fa853259a836b>`_) (**accounts**) - Rename from users and rework access control (alexander)

* (`693f5a9 <https://github.com/bizoxe/iron-track/commit/693f5a940d49a06e0a9fe22880d1ffbb91b3315f>`_) (**lib**) - Codebase refactoring and cleanup (alexander)

* (`d439929 <https://github.com/bizoxe/iron-track/commit/d4399290ffb573a76d206dab301690c99eeb573e>`_) (**db**) - Consolidate all ENUM creations into initial migration (alexander)

* (`34dd157 <https://github.com/bizoxe/iron-track/commit/34dd1573abf625c8b46b4245440b06acd90ca0d3>`_) (**server**) - Move logging and CLI into server layer (alexander)


🧪 Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`8feb433 <https://github.com/bizoxe/iron-track/commit/8feb433fbc9a907f5dbbc15cdb2998334b54deaa>`_) (**integration**) - Rewrite the integration suite (alexander)

* (`50260a4 <https://github.com/bizoxe/iron-track/commit/50260a40b4e8a71a5e3c8594a1049fac4635e441>`_) (**unit**) - Add filters, schemas and observability (alexander)

* (`493a5d0 <https://github.com/bizoxe/iron-track/commit/493a5d045733e2ba6cf1b814c12f2b5b2b830008>`_) (**integration**) - Rework integration conftest (alexander)

* (`95de119 <https://github.com/bizoxe/iron-track/commit/95de11922f4d5537ff48912fd9b650172f773ef1>`_) (**infra**) - Rework shared fixtures, seeds and helpers (alexander)


`Release [v0.2.0] - 2026-06-13 <https://github.com/bizoxe/iron-track/releases/tag/v0.2.0>`_
-----------------------------------------------------------------------------------------------------------------------

* `See All commits in v0.2.0 <https://github.com/bizoxe/iron-track/commits/v0.2.0>`_


⚙️ Miscellaneous Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`c0a527f <https://github.com/bizoxe/iron-track/commit/c0a527f43b4352a45b9726ad68b177c0c3389b62>`_) - Bump version to 0.2.0 (alexander)

* (`366c906 <https://github.com/bizoxe/iron-track/commit/366c9067cb20157436792315858cf9dd5ab37ed1>`_) - Save local changes before bumping version (alexander)

* (`d3f24bd <https://github.com/bizoxe/iron-track/commit/d3f24bdbfc0c515e39598786b52a9dcc76f512c5>`_) (**deps**) - Update project dependencies (alexander)

* (`0bc188e <https://github.com/bizoxe/iron-track/commit/0bc188e8ae17b631a262c4bf014623eada803a8c>`_) (**system**) - Remove async overhead from health logs (alexander)

* (`c9a1c37 <https://github.com/bizoxe/iron-track/commit/c9a1c37891bbba62a4c78e2e27d40944148d82fb>`_) (**infra**) - Pin postgres 18.3 and use custom config (alexander)

* (`28d2208 <https://github.com/bizoxe/iron-track/commit/28d2208f307391906ef6a2604270545042d4087a>`_) (**migrations**) - Generate alembic migration for exercise system (alexander)

* (`c69a2ba <https://github.com/bizoxe/iron-track/commit/c69a2baeccdf6e5a8fa7550c63d67cf41af844bb>`_) - Formalize repository infrastructure and optimize docs CI (alexander)


🐛 Bug Fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`04eb4ea <https://github.com/bizoxe/iron-track/commit/04eb4eac1d92c734151efef470df72563c80ed4d>`_) (**main**) - Fix CLI help handling (alexander)

* (`dffc73c <https://github.com/bizoxe/iron-track/commit/dffc73ced68447bce0e645ba20d2d4399313e6df>`_) (**scripts**) - Fix import in commands.py (alexander)

* (`a2e0ef2 <https://github.com/bizoxe/iron-track/commit/a2e0ef2a0c7988ec30997d7730cc80e3670effbc>`_) (**exercises**) - Use .is_(True) for system-default comparisons (alexander)

* (`7074953 <https://github.com/bizoxe/iron-track/commit/7074953901d06f02adb9c359822753cb5ddcb081>`_) (**users**) - Enforce timezone-aware datetimes in filters (alexander)


👷 CI/CD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`707d070 <https://github.com/bizoxe/iron-track/commit/707d0700d0167ccbea3920c8da8ef7d45b9178a9>`_) - Update actions and fix docs build environment (alexander)


📚 Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`3265145 <https://github.com/bizoxe/iron-track/commit/3265145c7672e113d36fa0227a73a28f44029140>`_) (**users**) - Update sphinx documentation (alexander)

* (`7ce9288 <https://github.com/bizoxe/iron-track/commit/7ce928844d1bb1ba53bdc0f1d2516cdb06facf37>`_) (**config**) - Update sphinx documentation (alexander)

* (`2a797e5 <https://github.com/bizoxe/iron-track/commit/2a797e521fc034ee9dd29237cb5573c03267c34a>`_) (**server**) - Update sphinx documentation (alexander)

* (`8b11188 <https://github.com/bizoxe/iron-track/commit/8b11188850f0168e023500df83f0c6cf78c12a94>`_) (**utils**) - Update sphinx documentation (alexander)

* (`5ed683d <https://github.com/bizoxe/iron-track/commit/5ed683d200af05f5becc54c1a6d3e70cc7923009>`_) (**lib**) - Update sphinx documentation (alexander)

* (`a37ffe2 <https://github.com/bizoxe/iron-track/commit/a37ffe2d3c339b8e054b21250ecf8f1401caa7cf>`_) (**catalogs**) - Add sphinx documentation (alexander)

* (`a046901 <https://github.com/bizoxe/iron-track/commit/a0469011fafd8ea0be76849f5e94a74349f89761>`_) (**exercises**) - Add sphinx documentation (alexander)

* (`2c300e3 <https://github.com/bizoxe/iron-track/commit/2c300e3f7c4262bd490243776a2471746d537bc9>`_) (**adr**) - Add Authentication and Serialization (alexander)

* (`b4ebcd7 <https://github.com/bizoxe/iron-track/commit/b4ebcd7064a2282947ca694c87930f4d7b83ff46>`_) (**benchmarks**) - Add authentication and serialization benchmark (alexander)

* (`532828e <https://github.com/bizoxe/iron-track/commit/532828ee4a7732d60f9329214ef2adc160b9da7f>`_) - Setup community health files (alexander)

* (`d36343b <https://github.com/bizoxe/iron-track/commit/d36343bf49a7221464619852ef36812ad099934f>`_) (**adr**) - Add stack rationale and update readme (alexander)

* (`8397d89 <https://github.com/bizoxe/iron-track/commit/8397d8960acd3f6acbe9835f699457063f311000>`_) (**readme**) - Add database blueprint [skip ci] (alexander)


📦 Build System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`a07d9cc <https://github.com/bizoxe/iron-track/commit/a07d9cceddf42784cac441897dfd0059b425c750>`_) (**deps**) - Bump codecov/codecov-action from 6 to 7 (#6) (dependabot[bot])

* (`caed57b <https://github.com/bizoxe/iron-track/commit/caed57bdc7936218249ecc48ca9821cb058c81b5>`_) (**deps**) - Bump softprops/action-gh-release from 2 to 3 (#4) (dependabot[bot])

* (`f21b3c0 <https://github.com/bizoxe/iron-track/commit/f21b3c0a1dde3c7dd896649e1a3418d7e81ad206>`_) (**scripts**) - Implement automated db seeding (alexander)

* (`cb72e96 <https://github.com/bizoxe/iron-track/commit/cb72e968f8ebf3aa490d8b01e74c9a1b4350ded4>`_) (**fixtures**) - Add exercise tags (alexander)


🚀 Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`746845a <https://github.com/bizoxe/iron-track/commit/746845adc38a69b52cc1f43549f829f243ae6da0>`_) (**users**) - Add case-insensitive email normalization (alexander)

* (`c6902a5 <https://github.com/bizoxe/iron-track/commit/c6902a5e1a4576bdb626e1d9119992056bcd977c>`_) (**domain**) - Implement CRUD operations for exercises (alexander)

* (`7665324 <https://github.com/bizoxe/iron-track/commit/76653242261ec3b8a194919630b4996e2bd3a35f>`_) (**domain**) - Implement CRUD operations for catalogs (alexander)

* (`65ca780 <https://github.com/bizoxe/iron-track/commit/65ca78040351bdea4f77b78f55cb40d2d884a957>`_) (**db**) - Add exercise and reference models with m2m relations (alexander)

* (`ef098da <https://github.com/bizoxe/iron-track/commit/ef098da3250492ce61afbd0775adc983a8869bac>`_) (**lib**) - Implement cache key normalization in CommonFilters (alexander)


🛠️ Refactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`3400259 <https://github.com/bizoxe/iron-track/commit/3400259eeeb475b81037023dbe0388623e2742fe>`_) (**ci**) - Unify and optimize CI/CD pipelines (alexander)

* (`76e568a <https://github.com/bizoxe/iron-track/commit/76e568a567756e1785b5ef9596c1a64ae19d8fc3>`_) (**users**) - Optimize data handling and authentication (alexander)

* (`db5ebd9 <https://github.com/bizoxe/iron-track/commit/db5ebd9ea75379c1042a1ac7c512cf322c316891>`_) (**lib**) - Cosmetic improvements and cleanup (alexander)

* (`819e95d <https://github.com/bizoxe/iron-track/commit/819e95d216e34bbb63a876de23d83a2804d7ac31>`_) (**lib**) - Externalize crypto thread pool configuration (alexander)

* (`63abf8d <https://github.com/bizoxe/iron-track/commit/63abf8d2370dc82cb0f3d885a29a067eb858b4ab>`_) (**logging**) - Optimize middleware and lifecycle management (alexander)

* (`b45abda <https://github.com/bizoxe/iron-track/commit/b45abda56ab5d54ee44e4fdda780b8b5dce84acd>`_) (**infra**) - Optimize resource limits and pgbouncer volume config (alexander)

* (`dd40b85 <https://github.com/bizoxe/iron-track/commit/dd40b85a11a5635a7cf0246e19dde873f88e0a0a>`_) (**scripts**) - Harden database seeding logic (alexander)

* (`dcbe85f <https://github.com/bizoxe/iron-track/commit/dcbe85fbc0dcc0bcd5dd0de83786421316cf0624>`_) (**catalogs**) - Rename utils.py to filters.py (alexander)

* (`29202ad <https://github.com/bizoxe/iron-track/commit/29202adcd484f0409517fbdc6e174e8f0caee9e3>`_) (**cli**) - Add multi-engine server support (Uvicorn/Granian) (alexander)

* (`96a7e27 <https://github.com/bizoxe/iron-track/commit/96a7e27f060796099ed9817477aae87dc644692d>`_) (**fixtures**) - Normalize exercise slugs and relative image paths (alexander)

* (`41291b0 <https://github.com/bizoxe/iron-track/commit/41291b0d0fc350d28ecdd2a1fa31ee1dcaa4fb2d>`_) - Optimize system performance and security baseline (alexander)


🧪 Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`56f70fa <https://github.com/bizoxe/iron-track/commit/56f70fad06af1ae552512b1b29bd7057cb368ba3>`_) - Refactor test data to use shared constants (alexander)

* (`64424ef <https://github.com/bizoxe/iron-track/commit/64424ef4032704d6086a22fd313aad88333c1a1a>`_) (**users**) - Adapt tests to architectural changes (alexander)

* (`89b755a <https://github.com/bizoxe/iron-track/commit/89b755a38196594243329b160b79f66c1a29d0c0>`_) (**exercises**) - Add integration tests (alexander)

* (`edf9418 <https://github.com/bizoxe/iron-track/commit/edf9418ede6a5c05a1034fb3e68954e240fa7c11>`_) (**users**) - Add special cases for activity, dates and sorting (alexander)

* (`9b37a2b <https://github.com/bizoxe/iron-track/commit/9b37a2b30011ab4015ee2914bc8b036ef2295df1>`_) (**catalogs**) - Add integration tests (alexander)


`Release [v0.1.0] - 2026-01-10 <https://github.com/bizoxe/iron-track/releases/tag/v0.1.0>`_
-----------------------------------------------------------------------------------------------------------------------

* `See All commits in v0.1.0 <https://github.com/bizoxe/iron-track/commits/v0.1.0>`_


⚙️ Miscellaneous Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`6a3e59b <https://github.com/bizoxe/iron-track/commit/6a3e59b69c1a586213b626d1eac0f9a47cbbee82>`_) (**certs**) - Update README.md (alexander)

* (`ed63919 <https://github.com/bizoxe/iron-track/commit/ed639194b3e87967a446e7a29cfc6fec3bb523dc>`_) (**lint**) - Allow local imports in tests data fixtures (alexander)

* (`41ec569 <https://github.com/bizoxe/iron-track/commit/41ec569a68e41abedde60b0926269f26db4730eb>`_) (**ci**) - Configure github actions and release tools (alexander)

* (`b02eeeb <https://github.com/bizoxe/iron-track/commit/b02eeeb06fd17296fd6d7e68d87d8668d16df823>`_) (**build**) - Configure Makefile (alexander)

* (`3211b88 <https://github.com/bizoxe/iron-track/commit/3211b887764105adcbc5a6f53160d900ee74098b>`_) (**build**) - Configure git-cliff (alexander)

* (`4520288 <https://github.com/bizoxe/iron-track/commit/45202889e7bc9c891c7aafa52ee833245894b50d>`_) - Configure bump-my-version for automated releases (alexander)

* (`ccbc75e <https://github.com/bizoxe/iron-track/commit/ccbc75eb8b57cc6462c0027c7f9758aa8d05ee2d>`_) - Configure sphinx build settings (alexander)

* (`92a44ec <https://github.com/bizoxe/iron-track/commit/92a44ecf18d0bee7422cfb1b1d559a8b0368a50d>`_) - Update and expand pre-commit hooks (alexander)

* (`8440a7e <https://github.com/bizoxe/iron-track/commit/8440a7ec8a697813ede05ec219bed65c373fce55>`_) (**db**) - Initialize Alembic database migrations (alexander)

* (`94f1712 <https://github.com/bizoxe/iron-track/commit/94f17124fae7a07e353242d5e4d00563bd9bbb30>`_) (**alembic**) - Remove old migration files from Git index prior to re-init (alexander)

* (`8cdaf2e <https://github.com/bizoxe/iron-track/commit/8cdaf2e1e84e21fea7910680e47b196e76a0cc73>`_) - Update dependencies and initialize project metadata (alexander)

* (`645c86c <https://github.com/bizoxe/iron-track/commit/645c86c630f2f5f6167a7cb7dc62a0b7c0ba47fa>`_) (**config**) - Update logging configuration (alexander)

* (`08eef8d <https://github.com/bizoxe/iron-track/commit/08eef8d701c057c6a4741c55f29f3bfafc11e031>`_) (**fixtures**) - Add system-default muscle_groups, equipment, and exercise JSON data (alexander)

* (`06266a2 <https://github.com/bizoxe/iron-track/commit/06266a2187d0cebbebdd80fbb4a37fad3dcd92db>`_) (**db**) - Add User + Role models (alexander)

* (`bd0f51f <https://github.com/bizoxe/iron-track/commit/bd0f51f46c8d52724fccb5427e50d5c685ecf551>`_) (**jwt_helpers**) - Add add_token_to_blacklist + is_token_in_blacklist funcs (alexander)

* (`38c1383 <https://github.com/bizoxe/iron-track/commit/38c1383eb0daa28cb2d437b276d831c46b657e48>`_) (**config**) - Update JWTSettings class (alexander)

* (`adfd6ba <https://github.com/bizoxe/iron-track/commit/adfd6ba198f06b77f5c6e920a6effafcea15dd30>`_) (**lib**) - Implement custom MsgPackCoderUserAuth class to encode/decode cache data (alexander)

* (`ea44aca <https://github.com/bizoxe/iron-track/commit/ea44acaa2feff9e968996f80352e17b441fa37fa>`_) (**deploy**) - Add Docker Compose stack for local development (alexander)

* (`f10a530 <https://github.com/bizoxe/iron-track/commit/f10a53086d968e1d72689474641438fdf80732eb>`_) (**deploy**) - Configure pgbouncer (alexander)

* (`cf0e31f <https://github.com/bizoxe/iron-track/commit/cf0e31f3c45e25e620cfbf5e69965ea6b6107062>`_) (**deploy**) - Configure postgres (alexander)

* (`ef0277d <https://github.com/bizoxe/iron-track/commit/ef0277de6c315f4c10e972042fd31d971fca9cd9>`_) (**users**) - Implement cli command to create system admin (alexander)

* (`9518258 <https://github.com/bizoxe/iron-track/commit/95182589630a1e670bfdd8e24dcbda4bda70024b>`_) (**lib**) - Add NotFoundException class (alexander)

* (`e3f44cf <https://github.com/bizoxe/iron-track/commit/e3f44cf9d42c4251821a42829942e85ddc38dd54>`_) (**config**) - Add application settings (alexander)

* (`e533a79 <https://github.com/bizoxe/iron-track/commit/e533a79885bf4e64b6b28a523fbb6b871a04c7f6>`_) (**users**) - Implement CLI command to create and assign default roles (alexander)

* (`c3a4158 <https://github.com/bizoxe/iron-track/commit/c3a41580d01bb91e03aad3c0aee39cdce21c5654>`_) (**lint**) - Update mypy + ruff configuration in pyproject.toml (alexander)

* (`4419314 <https://github.com/bizoxe/iron-track/commit/4419314e9e6cdd13a7adc70b244d387085b19723>`_) (**pre-commit**) - Add mypy hook (alexander)


⚡ Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`d8cb3b7 <https://github.com/bizoxe/iron-track/commit/d8cb3b7e70c6a4d96ff45e7ac9277581708f3303>`_) - Optimize infra for high-load and document benchmarks (alexander)

* (`45c7ecc <https://github.com/bizoxe/iron-track/commit/45c7eccd5f9ccc5594286d4ecd5d83714e20dbea>`_) (**users**) - Optimize user password update to avoid redundant SELECT query (alexander)


🐛 Bug Fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`7afcc39 <https://github.com/bizoxe/iron-track/commit/7afcc39cbd9b45760e323d47faa14d5b99825a99>`_) (**data**) - Fix typos in exercises and configure codespell ignores (alexander)

* (`03ee0df <https://github.com/bizoxe/iron-track/commit/03ee0dfb871c9341aeb7a642182b4e51f6784baf>`_) (**ci**) - Remove redundant frozen flag to fix uv sync conflict (alexander)

* (`c1bcb06 <https://github.com/bizoxe/iron-track/commit/c1bcb062852b8772b51d4b71041987f615fa1098>`_) (**cache**) - Switch user cache invalidation to direct Redis delete (alexander)

* (`deedf60 <https://github.com/bizoxe/iron-track/commit/deedf60d35da7fb3925c003ed76e70355a8d9597>`_) (**users**) - Add role_id in User CRUD by user create (alexander)


👷 CI/CD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`4137cc4 <https://github.com/bizoxe/iron-track/commit/4137cc443b1d929dc3f70c5c80fb23b5c421afdf>`_) - Disable automatic changelog commit to main (alexander)

* (`7eace6d <https://github.com/bizoxe/iron-track/commit/7eace6dd11c9e0e81a0793972fba87c98c18cfdb>`_) - Configure angie proxy with tls1.3, http3 and rate limiting (alexander)

* (`a51905c <https://github.com/bizoxe/iron-track/commit/a51905c93b43a0e2b58510fb980381dc4e5cbe13>`_) - Configure docker-compose.infra.yaml for local development (alexander)


📚 Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`d36efd1 <https://github.com/bizoxe/iron-track/commit/d36efd1a14b9d3d33410a27e54305d6f3b690a75>`_) - Finalize changelog for v0.1.0 (alexander)

* (`5815f5e <https://github.com/bizoxe/iron-track/commit/5815f5e0005a15753bfb59d864149b0c64c565ab>`_) - Update changelog for v0.1.0 (alexander)

* (`7eb6b84 <https://github.com/bizoxe/iron-track/commit/7eb6b8494ea5cb5852d9a22e2d78e4e03f91b8f4>`_) - Update changelog [skip ci] (github-actions[bot])

* (`c51d2ce <https://github.com/bizoxe/iron-track/commit/c51d2ce768061a3f10b26cdd70e7f098d399ee37>`_) (**system**) - Generate api documentation for system domain (alexander)

* (`136c3a6 <https://github.com/bizoxe/iron-track/commit/136c3a6bb278d51091c4aea4f5b52987a79e8b58>`_) - Update changelog [skip ci] (github-actions[bot])

* (`2fcab9c <https://github.com/bizoxe/iron-track/commit/2fcab9c19fbee5e6b47648289f46324a623fce36>`_) - Finalize README layout with  header and tech stack (alexander)

* (`9871551 <https://github.com/bizoxe/iron-track/commit/987155159855d51b08193f0ddcdc8b56f5106f90>`_) - Update changelog [skip ci] (github-actions[bot])

* (`c63e697 <https://github.com/bizoxe/iron-track/commit/c63e69758f2146a24e3b4ed29725122c39e246af>`_) - Update changelog [skip ci] (github-actions[bot])

* (`86b0b0f <https://github.com/bizoxe/iron-track/commit/86b0b0f418e9b6c379e062be074bbcd4373a1f35>`_) - Update changelog [skip ci] (github-actions[bot])

* (`c6be633 <https://github.com/bizoxe/iron-track/commit/c6be6331003f07fc54cce5ae8aad4427427bbc40>`_) - Add root index file and usage guide (alexander)

* (`e2f0412 <https://github.com/bizoxe/iron-track/commit/e2f0412b464966b5b54eeb892a138f418041bb37>`_) - Add CONTRIBUTING.rst with workflow and release guides (alexander)

* (`39904af <https://github.com/bizoxe/iron-track/commit/39904afaeb09d0e95862377532c6ae4d7f3c43d2>`_) (**scripts**) - Generate files for users management and db seeder (alexander)

* (`d6393df <https://github.com/bizoxe/iron-track/commit/d6393df5aa5ffc91ff4b806071d9e6979298dfea>`_) (**server**) - Generate files and add docstrings (alexander)

* (`c576d0c <https://github.com/bizoxe/iron-track/commit/c576d0cae9b9f249d6b779e093b9675240db7e20>`_) (**users**) - Generate files and update docstrings (alexander)

* (`8cdace5 <https://github.com/bizoxe/iron-track/commit/8cdace5b2fd6cf1b3ace74e6a1bc65f87b2487ea>`_) (**lib**) - Generate files and update docstrings (alexander)

* (`768e754 <https://github.com/bizoxe/iron-track/commit/768e75423f11bc6cf42d3ea43de3807196b7229d>`_) (**utils**) - Generate files and update docstrings (alexander)

* (`4c051fd <https://github.com/bizoxe/iron-track/commit/4c051fdf0b6589464a8cd351a0f8516aaf49869e>`_) (**cli**) - Generate files and update docstrings for main.py (alexander)

* (`4f6b05a <https://github.com/bizoxe/iron-track/commit/4f6b05a5ebc448f68bb78523644d7bd370e97410>`_) (**db**) - Generate files and update docstrings for user, role and base models (alexander)

* (`7a1cf0b <https://github.com/bizoxe/iron-track/commit/7a1cf0bbffd67f78c2ad32426a6636d6db10b3a2>`_) (**config**) - Generate files and update docstrings (alexander)

* (`3c3a786 <https://github.com/bizoxe/iron-track/commit/3c3a7863c0201690983da8cbefbcb6a570514523>`_) (**lib**) - Add docstrings for encode_jwt/decode_jwt functions (alexander)


📦 Build System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`f12bc0a <https://github.com/bizoxe/iron-track/commit/f12bc0a9785b67a80242e0e2c932d206dd1bfa19>`_) (**migrations**) - Add user_account and role tables (alexander)

* (`47dd84b <https://github.com/bizoxe/iron-track/commit/47dd84b73b4908b447f739192c204973bc8a4cf7>`_) (**system**) - Configure build backend to use Hatchling (alexander)


🚀 Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`916c4bf <https://github.com/bizoxe/iron-track/commit/916c4bf329a234933c956096effd5c0efccfb6c0>`_) - Implement multi-stage docker and angie orchestration (alexander)

* (`271016d <https://github.com/bizoxe/iron-track/commit/271016d3fc75cd0bdcc031432849ec060feb25c7>`_) (**deploy**) - Pin alpine version and tighten postgres security (alexander)

* (`a436738 <https://github.com/bizoxe/iron-track/commit/a436738b396cbda172a10d502ae27d8ba53d352b>`_) (**api**) - Configure healthcheck (alexander)

* (`4bf89fb <https://github.com/bizoxe/iron-track/commit/4bf89fb4083c4bcb46593f0a0711274573da394f>`_) (**cli**) - Introduce custom server commands with default entrypoint (alexander)

* (`b6cf415 <https://github.com/bizoxe/iron-track/commit/b6cf415d38085c858de65d25e81f27666e25c737>`_) (**deploy**) - Migrate PostgreSQL from v17 to v18 (alexander)

* (`95e0e1d <https://github.com/bizoxe/iron-track/commit/95e0e1d5e3cf5b6c241a6c16f40dce6dd573f46d>`_) (**core**) - Modernize application architecture and integrate services (alexander)

* (`68817b6 <https://github.com/bizoxe/iron-track/commit/68817b674071b991cec8b65590e9c18d5edae5df>`_) (**testing**) - Configure test environment, fixtures, and constants (alexander)

* (`f13e46c <https://github.com/bizoxe/iron-track/commit/f13e46c5d2af5fabecf25cfefe7437a33b1f57a0>`_) (**users**) - Implement full authentication and access management API (alexander)

* (`ef94601 <https://github.com/bizoxe/iron-track/commit/ef94601883112671a2223cf00f358413fbc71cf2>`_) (**users**) - Implement User CRUD endpoints (Requires Superuser) (alexander)

* (`2ebf21e <https://github.com/bizoxe/iron-track/commit/2ebf21e7f74afb62f27a466307e926fdc9d602c2>`_) (**users**) - Implement assign and revoke role (alexander)

* (`4776178 <https://github.com/bizoxe/iron-track/commit/477617894657e6f4f791103737b978cc6b72afab>`_) (**auth**) - Implement Authenticate class for user authentication/authorization (alexander)

* (`07fbd4b <https://github.com/bizoxe/iron-track/commit/07fbd4b1e0a72c5e5c781a188ac15b0c01c4d5af>`_) (**auth**) - Introduce JWTCookieSecurity for precise token handling (alexander)


🛠️ Refactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`068e581 <https://github.com/bizoxe/iron-track/commit/068e581f5f90933cba52769fd827aeaf966f0677>`_) (**ci**) - Secure JWT handling and update CodeQL (alexander)

* (`c6a748d <https://github.com/bizoxe/iron-track/commit/c6a748da5a8156ecbb70664e135da5438eda1f02>`_) (**users**) - Remove redundant password utility functions (alexander)

* (`b851e32 <https://github.com/bizoxe/iron-track/commit/b851e32d8d0764bccaa612cfe00887b2941ca3cd>`_) (**users**) - Integrate advanced-alchemy PasswordHash type (alexander)

* (`e83d6a8 <https://github.com/bizoxe/iron-track/commit/e83d6a8353d90c0b2d91c8d363c222f48f392100>`_) (**structure**) - Move application source code into 'src/app' directory (alexander)

* (`be0863e <https://github.com/bizoxe/iron-track/commit/be0863e187a380fb198537d11aad0b44807ec59f>`_) (**users**) - Update docstrings (alexander)

* (`1aa3a1c <https://github.com/bizoxe/iron-track/commit/1aa3a1cc8fa7b20923bc0c9d28f4f9dbaf622c5e>`_) (**cli**) - Centralize CLI logic and add user management group (alexander)

* (`d0a5e6c <https://github.com/bizoxe/iron-track/commit/d0a5e6c2362b6579f2c6697e399c30c973890c72>`_) (**cli**) - Use sqlalchemy_config.get_session() for direct session management (alexander)

* (`a9fb397 <https://github.com/bizoxe/iron-track/commit/a9fb397f09fd634c29a5898539581c95ee44141c>`_) (**deploy**) - Simplify pgbouncer entrypoint variable handling (alexander)

* (`e31f493 <https://github.com/bizoxe/iron-track/commit/e31f493fd0287a6f1a101ed95dbb1ceb73592581>`_) (**logging**) - Migrate logging to Stdout-only (alexander)

* (`f7f4d43 <https://github.com/bizoxe/iron-track/commit/f7f4d43af9e0f1e440d108efb300f27cf022b14f>`_) (**logging**) - Improve error handling and logging reliability in StructLogMiddleware (alexander)

* (`4a9f987 <https://github.com/bizoxe/iron-track/commit/4a9f98741c3b05e9443d404a59c82209e90c19da>`_) (**exceptions**) - Rename base class to BaseAPIException (alexander)

* (`4e9d720 <https://github.com/bizoxe/iron-track/commit/4e9d7202ab58cb3d9f26203cdcfeabd224a6b4ae>`_) (**lib**) - Reuse global msgspec JSON objects (alexander)


🧪 Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* (`294eb61 <https://github.com/bizoxe/iron-track/commit/294eb61eb208f4f88205b056ae57681b78c651c9>`_) (**system**) - Add tests for system health (alexander)

* (`476c6ce <https://github.com/bizoxe/iron-track/commit/476c6ce582eecd19e903693c0b5d0a01fd4cb957>`_) (**users**) - Add tests for users, roles and access controllers (alexander)

IronTrack Changelog
