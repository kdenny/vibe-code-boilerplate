"""Combinatorial / integration suites for real cross-module compose seams.

Unit tests under ``tests/test_<module>.py`` cover one module in isolation.
The suites in this package cover *seams* — two or more modules that are
**designed to compose** in the product — exercising the real collaborators and
mocking only the true I/O boundary (network, subprocess, filesystem edge).

Add a suite here only for a seam that actually exists in the product, and wire
it into ``lib/vibe/testscope.py``'s ``INTEGRATION_SEAMS`` so a change to either
side runs it. See ``recipes/testing/modular-testing.md``.
"""
