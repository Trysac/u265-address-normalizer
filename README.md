# address-normalizer

[![PyPI version](https://img.shields.io/pypi/v/trysac-address-normalizer)](https://pypi.org/project/trysac-address-normalizer/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-address-normalizer)](LICENSE)
[![CI](https://github.com/Trysac/u265-address-normalizer/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u265-address-normalizer/actions/workflows/ci.yml)

Normalize postal addresses with explicit per-country rules: USPS Publication 28 abbreviations for the US, Royal Mail postcode format for GB and Canada Post codes for CA, with a change log

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-address-normalizer
# or
uv add trysac-address-normalizer
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import address_normalizer

# normalize() trims surrounding whitespace and lower-cases the text.
print(address_normalizer.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    address_normalizer.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
