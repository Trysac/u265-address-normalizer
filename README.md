# trysac-address-normalizer

Address data from forms and imports mixes 'Street', 'St.' and 'st', lowercase states and postcodes without their space, so deduplication, geocoding and shipping labels fail on records that are really the same. This library applies a small, documented rule set per country and reports every change it made.

## Features

- Frozen dataclasses `Address`, `Change`, `Result`; immutable `CountryRules` and bundled `RULES`.
- Supported countries: `US`, `GB`, `CA`; the country code is uppercased.
- Common steps: Unicode NFKC, collapse whitespace runs to one space and trim; `line1` and `country` are required.
- US: uppercase `line1`, `line2`, `city`, `region`; remove punctuation except `#`, `-`, `/`; abbreviate directionals, suffixes and unit designators; validate region against the bundled state, possession and military codes (the 59 Appendix B codes plus AA, AE, AP); format ZIP as `NNNNN` or `NNNNN-NNNN`.
- GB: uppercase city, keep region text, format postcode as `SW1A 1AA`; only `line1` and `country` are required.
- CA: uppercase `line1`, `line2`, `city`, `region`; validate province against `AB BC MB NB NL NS NT NU ON PE QC SK YT`; format postal code as `K1A 0B1`.
- `normalize` returns changes sorted by field and rule and deduplicated.
- `normalize_postal_code(code, country)` applies only the country's postcode rule.

## Installation

```bash
pip install trysac-address-normalizer
```

## Usage

```python
from address_normalizer import Address, normalize, normalize_postal_code

result = normalize(
    Address(
        line1="123 north main street apartment 4",
        city="springfield",
        region="il",
        postal_code="627011234",
        country="US",
    )
)
assert result.address.line1 == "123 N MAIN ST APT 4"
assert result.address.postal_code == "62701-1234"
assert normalize_postal_code("sw1a1aa", "GB") == "SW1A 1AA"
```

## Public API

- `normalize(address: Address, *, rules: Mapping[str, CountryRules] | None = None) -> Result` -- normalizes an `Address`; optional `rules` replaces the bundled `RULES`.
- `normalize_postal_code(code: str, country: str) -> str` -- applies only the postcode rule for `US`, `GB` or `CA`.
- `Address(line1, line2='', city='', region='', postal_code='', country='')`, `Change(field, rule)`, `Result(address, changes)`, `CountryRules`, `RULES`.
- `AddressError.code` is one of `unsupported_country`, `invalid_region`, `invalid_postal_code`, `input_too_large`, `missing_field`.
- Limits: every field is at most 200 characters after NFKC; `line1` and `country` must be non-empty. Supported countries are `US`, `GB`, `CA` when using bundled `RULES`.

## Why not libpostal

libpostal is a large parser trained on addresses and does not report field-level changes. This package is stdlib-only, applies deterministic per-country rules, and returns an explicit `Change` log for each field it altered.

## Documentation

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model, [docs/PROJECT.md](docs/PROJECT.md) for scope, and [docs/TESTING.md](docs/TESTING.md) for the test suite.
