"""LLM gateway: the only module that talks to model providers (T-005, ADR-003, ADR-016).

Public API: ``LLMGateway.complete_structured`` (+ ``LLMResult``, ``LLMOutputError``,
``LLMUnavailableError``), ``PromptTemplate`` / ``registry`` for feature prompts.
"""
