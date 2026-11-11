# Security notes

## Threat model

`trysac-address-normalizer` is a pure, standard-library-only library with no network, file, database or subprocess I/O in the package. It does not log addresses; the module installs `logging.NullHandler()`.

Defended:
- Untrusted field strings: every field is NFKC-normalized and checked against `MAX_FIELD_LENGTH = 200`; oversize input raises `AddressError('input_too_large')`.
- Missing required fields: empty `line1` or `country` after whitespace collapse raises `AddressError('missing_field')`.
- Unsupported countries and invalid region/postcode formats raise `AddressError` with the specific code; the library never silently accepts a country it has no rules for.
- No `eval`, `exec`, deserialization of untrusted data, or runtime dependency supply chain.

Not defended:
- The caller's handling of normalized addresses after return, including storage, display and logging; addresses are personal data.
- Address validation against official postal databases; the rules only check bundled region codes and postcode patterns.
- Free-text parsing or geocoding; there is no such feature.
- Denial of service through request volume; only per-field size is limited.
- Other countries or region-name-to-code conversion; those are out of scope.

## Publishing

The package has no runtime dependencies. Release credentials and repository publishing controls are managed outside this library; do not embed secrets in source or tests. To report a vulnerability, use the repository's issue tracker.
