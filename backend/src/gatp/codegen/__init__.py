"""Codegen: approved test plan -> pytest-playwright Page Object code + validation (T-013).

``render`` is deterministic (no model call); ``validate`` checks syntax, verified locators and
safety statically; the runner's ``recount`` and ``collect`` jobs check the code live.
"""
