from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

__all__ = [
    "RULES",
    "Address",
    "AddressError",
    "Change",
    "CountryRules",
    "Result",
    "normalize",
    "normalize_postal_code",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AddressError(Exception):
    """Raised when address normalization cannot be completed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Address:
    line1: str
    line2: str = ""
    city: str = ""
    region: str = ""
    postal_code: str = ""
    country: str = ""


@dataclass(frozen=True)
class Change:
    field: str
    rule: Literal[
        "case",
        "whitespace",
        "punctuation",
        "directional",
        "suffix",
        "unit",
        "postal_code",
    ]


@dataclass(frozen=True)
class Result:
    address: Address
    changes: tuple[Change, ...]


@dataclass(frozen=True)
class CountryRules:
    """Immutable description of per-country normalization rules."""

    uppercase_line1: bool = False
    uppercase_line2: bool = False
    uppercase_city: bool = False
    uppercase_region: bool = False
    remove_punctuation: bool = False
    apply_directional: bool = False
    apply_suffix: bool = False
    apply_unit: bool = False
    region_codes: frozenset[str] | None = None
    postal_code_rule: str = "none"


# ---------------------------------------------------------------------------
# Constants from USPS Publication 28 (Appendix B, C1, C2) and Canada Post
# ---------------------------------------------------------------------------

MAX_FIELD_LENGTH: Final[int] = 200

_DIRECTIONAL_ABBREVIATIONS: Final[dict[str, str]] = {
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
    "NORTHEAST": "NE",
    "NORTHWEST": "NW",
    "SOUTHEAST": "SE",
    "SOUTHWEST": "SW",
}

_SUFFIX_ABBREVIATIONS: Final[dict[str, str]] = {
    "STREET": "ST",
    "AVENUE": "AVE",
    "BOULEVARD": "BLVD",
    "ROAD": "RD",
    "DRIVE": "DR",
    "LANE": "LN",
    "COURT": "CT",
    "PLACE": "PL",
    "TERRACE": "TER",
    "HIGHWAY": "HWY",
    "PARKWAY": "PKWY",
    "CIRCLE": "CIR",
}

_UNIT_ABBREVIATIONS: Final[dict[str, str]] = {
    "APARTMENT": "APT",
    "SUITE": "STE",
    "BUILDING": "BLDG",
    "FLOOR": "FL",
    "ROOM": "RM",
    "UNIT": "UNIT",  # already standard
}

_DESIGNATORS: Final[frozenset[str]] = frozenset(
    set(_UNIT_ABBREVIATIONS.keys()) | set(_UNIT_ABBREVIATIONS.values()) | {"#"}
)

_USA_REGION_CODES: Final[frozenset[str]] = frozenset(
    {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
        "AS",
        "FM",
        "GU",
        "MH",
        "MP",
        "PW",
        "PR",
        "VI",
        "AA",
        "AE",
        "AP",
    }
)

_CA_REGION_CODES: Final[frozenset[str]] = frozenset(
    {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}
)

RULES: Final[Mapping[str, CountryRules]] = {
    "US": CountryRules(
        uppercase_line1=True,
        uppercase_line2=True,
        uppercase_city=True,
        uppercase_region=True,
        remove_punctuation=True,
        apply_directional=True,
        apply_suffix=True,
        apply_unit=True,
        region_codes=_USA_REGION_CODES,
        postal_code_rule="us",
    ),
    "GB": CountryRules(
        uppercase_city=True,
        postal_code_rule="gb",
    ),
    "CA": CountryRules(
        uppercase_line1=True,
        uppercase_line2=True,
        uppercase_city=True,
        uppercase_region=True,
        region_codes=_CA_REGION_CODES,
        postal_code_rule="ca",
    ),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _collapse_whitespace(value: str) -> str:
    """Collapse runs of whitespace to a single space and trim."""
    return " ".join(value.split())


def _remove_punctuation_us(value: str) -> str:
    """Remove punctuation except '#' , '-' and '/' from a string."""
    return re.sub(r"[^A-Za-z0-9\s#\-/]", "", value)


def _normalize_postal_code_us(code: str) -> str:
    """Normalize a US ZIP code. Assumes NFKC and whitespace are already applied."""
    digits = re.sub(r"[\s\-]", "", code)
    if len(digits) == 5 and digits.isdigit():
        return digits
    if len(digits) == 9 and digits.isdigit():
        return f"{digits[:5]}-{digits[5:]}"
    raise AddressError("invalid_postal_code")


def _normalize_postal_code_gb(code: str) -> str:
    """Normalize a UK postcode. Assumes NFKC and whitespace are applied."""
    cleaned = re.sub(r"\s", "", code).upper()
    pattern = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2}$")
    if pattern.match(cleaned) or cleaned == "GIR0AA":
        return f"{cleaned[:-3]} {cleaned[-3:]}".strip()
    raise AddressError("invalid_postal_code")


def _normalize_postal_code_ca(code: str) -> str:
    """Normalize a Canadian postal code. Assumes NFKC and whitespace are applied."""
    cleaned = re.sub(r"\s", "", code).upper()
    pattern = re.compile(r"^[ABCEGHJ-NPRSTVXY][0-9][ABCEGHJ-NPRSTV-Z][0-9][ABCEGHJ-NPRSTV-Z][0-9]$")
    if pattern.match(cleaned):
        return f"{cleaned[:3]} {cleaned[3:]}"
    raise AddressError("invalid_postal_code")


def _normalize_postal_code_raw(code: str, country: str) -> str:
    """Apply NFKC, whitespace collapse, then country-specific postcode rule."""
    nfkc = unicodedata.normalize("NFKC", code)
    if len(nfkc) > MAX_FIELD_LENGTH:
        raise AddressError("input_too_large")
    collapsed = _collapse_whitespace(nfkc)
    country_upper = country.upper()
    if country_upper not in RULES:
        raise AddressError("unsupported_country")
    rule = RULES[country_upper].postal_code_rule
    if rule == "us":
        return _normalize_postal_code_us(collapsed)
    if rule == "gb":
        return _normalize_postal_code_gb(collapsed)
    if rule == "ca":
        return _normalize_postal_code_ca(collapsed)
    # No postcode rule
    return collapsed


def _process_line1_us(line1: str) -> tuple[str, list[Change]]:
    """Apply USPS Publication 28 rules to line1 (directional/suffix/unit)."""
    changes: list[Change] = []
    original = line1
    unit_changed = False

    # Split '#4' into '# 4' if present
    if re.search(r"#\d", line1):
        line1 = re.sub(r"#(\d)", r"# \1", line1)
        unit_changed = True

    tokens = line1.split()
    if len(tokens) < 2:
        if unit_changed:
            changes.append(Change("line1", "unit"))
        return line1, changes

    house = tokens[0]
    rest = tokens[1:]
    street_tokens: list[str] = []
    unit_tokens: list[str] = []

    # Find unit designator
    for i, token in enumerate(rest):
        if token in _DESIGNATORS and i + 1 < len(rest):
            street_tokens = rest[:i]
            unit_tokens = rest[i:]
            break
    else:
        street_tokens = rest

    # Directional processing on street_tokens
    if len(street_tokens) >= 3 and street_tokens[0] in _DIRECTIONAL_ABBREVIATIONS:
        abbr = _DIRECTIONAL_ABBREVIATIONS[street_tokens[0]]
        if abbr != street_tokens[0]:
            street_tokens[0] = abbr
            changes.append(Change("line1", "directional"))

    if (
        len(street_tokens) >= 3
        and street_tokens[-1] in _DIRECTIONAL_ABBREVIATIONS
        and street_tokens[-2] not in _SUFFIX_ABBREVIATIONS
        and street_tokens[-2] not in _SUFFIX_ABBREVIATIONS.values()
    ):
        abbr = _DIRECTIONAL_ABBREVIATIONS[street_tokens[-1]]
        if abbr != street_tokens[-1]:
            street_tokens[-1] = abbr
            changes.append(Change("line1", "directional"))

    # Suffix abbreviation: the last street word that is a suffix designator.
    # Directional words at the end are street-name words, never suffixes.
    for suffix_index in range(len(street_tokens) - 1, -1, -1):
        token = street_tokens[suffix_index]
        if token in _SUFFIX_ABBREVIATIONS or token in _SUFFIX_ABBREVIATIONS.values():
            suffix_abbr = _SUFFIX_ABBREVIATIONS.get(token)
            if suffix_abbr is not None and suffix_abbr != token:
                street_tokens[suffix_index] = suffix_abbr
                changes.append(Change("line1", "suffix"))
            break

    # Unit abbreviation
    if unit_tokens:
        first = unit_tokens[0]
        if first in _UNIT_ABBREVIATIONS and _UNIT_ABBREVIATIONS[first] != first:
            unit_tokens[0] = _UNIT_ABBREVIATIONS[first]
            unit_changed = True
        # If first is '#', no abbreviation.
    if unit_changed:
        changes.append(Change("line1", "unit"))

    parts = [house]
    if street_tokens:
        parts.append(" ".join(street_tokens))
    if unit_tokens:
        parts.append(" ".join(unit_tokens))
    new_line1 = " ".join(parts)
    if new_line1 != original and not unit_changed:
        # Safeguard: if something changed unexpectedly without a rule recorded,
        # record a whitespace change (should not normally happen).
        pass
    return new_line1, changes


def _process_line2_us(line2: str) -> tuple[str, list[Change]]:
    """Apply unit designator abbreviation to line2 for US."""
    changes: list[Change] = []
    original = line2
    unit_changed = False

    if re.search(r"#\d", line2):
        line2 = re.sub(r"#(\d)", r"# \1", line2)
        unit_changed = True

    tokens = line2.split()
    if len(tokens) >= 2 and tokens[0] in _UNIT_ABBREVIATIONS:
        abbr = _UNIT_ABBREVIATIONS[tokens[0]]
        if abbr != tokens[0]:
            tokens[0] = abbr
            unit_changed = True

    new_line2 = " ".join(tokens)
    if unit_changed:
        changes.append(Change("line2", "unit"))
    if new_line2 != original and not unit_changed:
        # Should not happen, but record whitespace if accidental.
        pass
    return new_line2, changes


def normalize(address: Address, *, rules: Mapping[str, CountryRules] | None = None) -> Result:
    """Normalize an address according to per-country rules.

    Args:
        address: The address to normalize.
        rules: Optional mapping of country code to CountryRules. If omitted,
            the bundled RULES for 'US', 'GB' and 'CA' are used.

    Returns:
        A Result containing the normalized address and a sorted, unique tuple
        of Change objects describing what was altered.

    Raises:
        AddressError: If the country is unsupported, a region is invalid, a
            postal code is invalid, a field exceeds the size limit, or a
            required field is missing.
    """
    rule_map = rules if rules is not None else RULES
    changes: list[Change] = []

    # Step 1: NFKC and size check for every field
    fields = {
        "line1": address.line1,
        "line2": address.line2,
        "city": address.city,
        "region": address.region,
        "postal_code": address.postal_code,
        "country": address.country,
    }
    nfkc_fields: dict[str, str] = {}
    for name, value in fields.items():
        nfkc = unicodedata.normalize("NFKC", value)
        if len(nfkc) > MAX_FIELD_LENGTH:
            raise AddressError("input_too_large")
        nfkc_fields[name] = nfkc

    # Step 2: whitespace collapse and required-field check
    collapsed_fields: dict[str, str] = {}
    for name, value in nfkc_fields.items():
        collapsed = _collapse_whitespace(value)
        collapsed_fields[name] = collapsed
        if collapsed != value:
            changes.append(Change(name, "whitespace"))
    if not collapsed_fields["line1"]:
        raise AddressError("missing_field")
    if not collapsed_fields["country"]:
        raise AddressError("missing_field")

    # Step 3: Country-specific transformations
    country = collapsed_fields["country"].upper()
    if country != collapsed_fields["country"]:
        changes.append(Change("country", "case"))
    collapsed_fields["country"] = country

    if country not in rule_map:
        raise AddressError("unsupported_country")
    cr = rule_map[country]

    # line1
    line1 = collapsed_fields["line1"]
    if cr.uppercase_line1:
        new = line1.upper()
        if new != line1:
            changes.append(Change("line1", "case"))
            line1 = new
    if cr.remove_punctuation:
        new = _remove_punctuation_us(line1)
        if new != line1:
            changes.append(Change("line1", "punctuation"))
            line1 = new
    if cr.apply_directional or cr.apply_suffix or cr.apply_unit:
        line1, line1_changes = _process_line1_us(line1)
        changes.extend(line1_changes)
    collapsed_fields["line1"] = line1

    # line2
    line2 = collapsed_fields["line2"]
    if cr.uppercase_line2:
        new = line2.upper()
        if new != line2:
            changes.append(Change("line2", "case"))
            line2 = new
    if cr.remove_punctuation:
        new = _remove_punctuation_us(line2)
        if new != line2:
            changes.append(Change("line2", "punctuation"))
            line2 = new
    if cr.apply_unit:
        line2, line2_changes = _process_line2_us(line2)
        changes.extend(line2_changes)
    collapsed_fields["line2"] = line2

    # city
    city = collapsed_fields["city"]
    if cr.uppercase_city:
        new = city.upper()
        if new != city:
            changes.append(Change("city", "case"))
            city = new
    if cr.remove_punctuation:
        new = _remove_punctuation_us(city)
        if new != city:
            changes.append(Change("city", "punctuation"))
            city = new
    collapsed_fields["city"] = city

    # region
    region = collapsed_fields["region"]
    if cr.uppercase_region:
        new = region.upper()
        if new != region:
            changes.append(Change("region", "case"))
            region = new
    if cr.region_codes is not None and region and region not in cr.region_codes:
        raise AddressError("invalid_region")
    collapsed_fields["region"] = region

    # postal code (optional: only validated when present)
    postal = collapsed_fields["postal_code"]
    if cr.postal_code_rule != "none" and postal:
        try:
            if cr.postal_code_rule == "us":
                new_postal = _normalize_postal_code_us(postal)
            elif cr.postal_code_rule == "gb":
                new_postal = _normalize_postal_code_gb(postal)
            elif cr.postal_code_rule == "ca":
                new_postal = _normalize_postal_code_ca(postal)
            else:
                new_postal = postal
        except AddressError as exc:
            if exc.code == "invalid_postal_code":
                raise
            # Unreachable for these rules
            raise
        if new_postal != postal:
            changes.append(Change("postal_code", "postal_code"))
            postal = new_postal
    collapsed_fields["postal_code"] = postal

    new_address = Address(
        line1=collapsed_fields["line1"],
        line2=collapsed_fields["line2"],
        city=collapsed_fields["city"],
        region=collapsed_fields["region"],
        postal_code=collapsed_fields["postal_code"],
        country=collapsed_fields["country"],
    )

    # Deduplicate and sort changes
    unique_changes: dict[tuple[str, str], Change] = {}
    for ch in changes:
        key = (ch.field, ch.rule)
        if key not in unique_changes:
            unique_changes[key] = ch
    sorted_changes = tuple(
        unique_changes[key] for key in sorted(unique_changes.keys(), key=lambda x: (x[0], x[1]))
    )
    return Result(address=new_address, changes=sorted_changes)


def normalize_postal_code(code: str, country: str) -> str:
    """Normalize a postal code according to the country's rule.

    This function applies only the postcode transformation for the given
    country (US, GB, CA). It does not validate region or other fields.

    Args:
        code: The postal code to normalize.
        country: The country code (case-insensitive).

    Returns:
        The normalized postal code.

    Raises:
        AddressError: If the country is unsupported, the code is invalid, or
            the code exceeds the size limit.
    """
    return _normalize_postal_code_raw(code, country)
