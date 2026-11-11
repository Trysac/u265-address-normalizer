# Project record

## Objective

Normalize postal addresses with explicit per-country rules: USPS Publication 28 abbreviations for the US, Royal Mail postcode format for GB and Canada Post codes for CA, with a change log.

## Scope

- Public API in `address_normalizer`: `Address`, `Change`, `Result`, `CountryRules`, `RULES`, `AddressError`, `normalize`, `normalize_postal_code`.
- Bundled rules for `US`, `GB`, `CA`; common NFKC and whitespace normalization; change reporting sorted by `(field, rule)` and deduplicated.
- Field size limit of 200 characters after NFKC; `line1` and `country` required.
- `AddressError` codes: `unsupported_country`, `invalid_region`, `invalid_postal_code`, `input_too_large`, `missing_field`.

## Out of scope

- Parsing free-text addresses into fields.
- Geocoding.
- Address validation against official databases.
- Countries other than `US`, `GB`, `CA`.
- State names to codes.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays 'pending measurement'.

| Metric | Value |
|---|---|
| Tokens (input / output) | 1007310 / 84580 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1140 |

## Factory run u265 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-11 | generation | deepseek-v4-pro | yes | 1913 | 22530 | 0 | 3328 | 0.0459 |
| 2026-11-11 | fix-1 | deepseek-flash | no | 12681 | 6375 | 0 | 92672 | 0.0060 |
| 2026-11-11 | fix-2 | deepseek-flash | no | 7681 | 421 | 0 | 22912 | 0.0015 |
| 2026-11-11 | audit | deepseek-flash | no | 33269 | 37584 | 0 | 416384 | 0.0288 |
| 2026-11-11 | threat-model | deepseek-flash | no | 32297 | 9478 | 0 | 280832 | 0.0114 |
| 2026-11-11 | docs | deepseek-flash | no | 103085 | 8192 | 0 | 256 | 0.0204 |

Total: $0.1140. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
