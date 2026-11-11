# Address normalization library with explicit per-country rules

Status: accepted (generated, pending human review)

## Context

The repository needed a small, deterministic address normalizer that reports every change it makes, unlike large opaque parsers.

## Decision

Implement a Python library with frozen dataclasses and a rule-based engine that applies USPS Publication 28 (US), Royal Mail (GB), and Canada Post (CA) rules. An explicit change log records each transformation.

## Consequences

The library is auditable and testable. It is intentionally limited to three countries and does not geocode or validate against official databases. Adding new countries requires extending the rule engine and tests.
