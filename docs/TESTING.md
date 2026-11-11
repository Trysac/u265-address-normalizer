# Testing

## Running

```sh
python -m pytest tests/test_address_normalizer.py
```

## Policy

- Tests call the public API `address_normalizer`.
- They assert normalized addresses, change tuples, and `AddressError.code` values.
- They cover the acceptance cases in the specification: US full example, line1 suffix/punctuation and line2 unit, invalid region/postal/country, 200/201 character limit, missing required fields, and GB/CA postal code formatting and invalid codes.
- No property-based or external conformance tests are present.

## Tiers

The tests are a single pytest tier. No conformance tests, external tools, downloads, markers or CI-only setup are present in the repository code.

## Layout

`tests/test_address_normalizer.py` contains all tests. There is no `tests/conftest.py` in the repository code.
