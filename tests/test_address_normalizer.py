from __future__ import annotations

import pytest

from address_normalizer import (
    Address,
    AddressError,
    Change,
    CountryRules,
    normalize,
    normalize_postal_code,
)


def test_acceptance_us_full_example() -> None:
    addr = Address(
        line1="123 north main street apartment 4",
        city="springfield",
        region="il",
        postal_code="627011234",
        country="US",
    )
    result = normalize(addr)
    expected_addr = Address(
        line1="123 N MAIN ST APT 4",
        line2="",
        city="SPRINGFIELD",
        region="IL",
        postal_code="62701-1234",
        country="US",
    )
    assert result.address == expected_addr
    expected_changes = tuple(
        sorted(
            [
                Change("city", "case"),
                Change("line1", "case"),
                Change("line1", "directional"),
                Change("line1", "suffix"),
                Change("line1", "unit"),
                Change("postal_code", "postal_code"),
                Change("region", "case"),
            ],
            key=lambda c: (c.field, c.rule),
        )
    )
    assert result.changes == expected_changes


def test_acceptance_line1_suffix_and_punctuation() -> None:
    # '10 Avenue Road' -> '10 AVENUE RD'
    r1 = normalize(Address(line1="10 Avenue Road", country="US"))
    assert r1.address.line1 == "10 AVENUE RD"
    assert Change("line1", "suffix") in r1.changes
    assert Change("line1", "case") in r1.changes

    # '500 Main St.' -> '500 MAIN ST'
    r2 = normalize(Address(line1="500 Main St.", country="US"))
    assert r2.address.line1 == "500 MAIN ST"
    assert Change("line1", "punctuation") in r2.changes

    # line2 'Suite 200' -> 'STE 200'
    r3 = normalize(Address(line1="123 Main St", line2="Suite 200", country="US"))
    assert r3.address.line2 == "STE 200"
    assert Change("line2", "case") in r3.changes
    assert Change("line2", "unit") in r3.changes


def test_acceptance_invalid_region_postal_country() -> None:
    with pytest.raises(AddressError) as exc_info:
        normalize(Address(line1="123 Main St", region="ZZ", country="US"))
    assert exc_info.value.code == "invalid_region"

    with pytest.raises(AddressError) as exc_info:
        normalize(Address(line1="123 Main St", postal_code="1234", country="US"))
    assert exc_info.value.code == "invalid_postal_code"

    with pytest.raises(AddressError) as exc_info:
        normalize(Address(line1="123 Main St", country="FR"))
    assert exc_info.value.code == "unsupported_country"


def test_acceptance_size_limit() -> None:
    long_field = "a" * 201
    with pytest.raises(AddressError) as exc_info:
        normalize(Address(line1=long_field, country="US"))
    assert exc_info.value.code == "input_too_large"

    # 200 chars accepted
    ok_field = "a" * 200
    r = normalize(Address(line1=ok_field, country="US"))
    assert r.address.line1 == ok_field.upper()


def test_acceptance_missing_required_fields() -> None:
    with pytest.raises(AddressError) as exc_info:
        normalize(Address(line1="", country="US"))
    assert exc_info.value.code == "missing_field"

    with pytest.raises(AddressError) as exc_info:
        normalize(Address(line1="123 Main St", country=""))
    assert exc_info.value.code == "missing_field"


def test_acceptance_postal_codes() -> None:
    assert normalize_postal_code("sw1a1aa", "GB") == "SW1A 1AA"
    assert normalize_postal_code("gir0aa", "GB") == "GIR 0AA"
    with pytest.raises(AddressError) as exc_info:
        normalize_postal_code("SW1A1A", "GB")
    assert exc_info.value.code == "invalid_postal_code"

    assert normalize_postal_code("k1a0b1", "CA") == "K1A 0B1"
    with pytest.raises(AddressError) as exc_info:
        normalize_postal_code("D1A 0B1", "CA")
    assert exc_info.value.code == "invalid_postal_code"

    assert normalize_postal_code("12345", "US") == "12345"
    assert normalize_postal_code("12345-6789", "US") == "12345-6789"
    assert normalize_postal_code("123456789", "US") == "12345-6789"
    with pytest.raises(AddressError) as exc_info:
        normalize_postal_code("1234", "US")
    assert exc_info.value.code == "invalid_postal_code"


def test_ca_region_and_case() -> None:
    r = normalize(
        Address(
            line1="123 main st", city="toronto", region="on", postal_code="k1a 0b1", country="CA"
        )
    )
    assert r.address.line1 == "123 MAIN ST"
    assert r.address.city == "TORONTO"
    assert r.address.region == "ON"
    assert r.address.postal_code == "K1A 0B1"
    assert Change("line1", "case") in r.changes
    assert Change("region", "case") in r.changes
    assert Change("postal_code", "postal_code") in r.changes

    with pytest.raises(AddressError) as exc_info:
        normalize(Address(line1="123 Main St", region="XX", country="CA"))
    assert exc_info.value.code == "invalid_region"


def test_gb_rules() -> None:
    # GB: lines not uppercased, city uppercased, region kept, postcode formatted
    addr = Address(
        line1="10 downing street",
        city="london",
        region="Greater London",
        postal_code="sw1a1aa",
        country="GB",
    )
    r = normalize(addr)
    assert r.address.line1 == "10 downing street"
    assert r.address.city == "LONDON"
    assert r.address.region == "Greater London"
    assert r.address.postal_code == "SW1A 1AA"
    assert Change("city", "case") in r.changes
    assert Change("postal_code", "postal_code") in r.changes
    assert Change("line1", "case") not in r.changes


def test_idempotence() -> None:
    addrs = [
        Address(
            line1="123 north main street apartment 4",
            city="springfield",
            region="il",
            postal_code="627011234",
            country="US",
        ),
        Address(line1="500 Main St.", country="US"),
        Address(line1="123 Main St", line2="Suite 200", country="US"),
        Address(
            line1="10 downing street",
            city="london",
            region="Greater London",
            postal_code="sw1a1aa",
            country="GB",
        ),
        Address(
            line1="123 main st", city="toronto", region="on", postal_code="k1a 0b1", country="CA"
        ),
    ]
    for addr in addrs:
        first = normalize(addr)
        second = normalize(first.address)
        assert second.address == first.address
        assert second.changes == ()


def test_whitespace_collapse_and_record() -> None:
    addr = Address(
        line1="  123   North   Main   Street  ",
        city="Springfield  ",
        country=" US ",
    )
    r = normalize(addr)
    assert r.address.line1 == "123 N MAIN ST"
    assert r.address.city == "SPRINGFIELD"
    assert r.address.country == "US"
    # whitespace changes recorded
    assert Change("line1", "whitespace") in r.changes
    assert Change("city", "whitespace") in r.changes
    assert Change("country", "whitespace") in r.changes


def test_case_country_upper() -> None:
    r = normalize(Address(line1="123 main st", country="us"))
    assert r.address.country == "US"
    assert Change("country", "case") in r.changes


def test_custom_rules_mapping() -> None:
    custom = {
        "XX": CountryRules(
            uppercase_line1=True,
            postal_code_rule="none",
        )
    }
    r = normalize(Address(line1="hello world", country="xx"), rules=custom)
    assert r.address.line1 == "HELLO WORLD"
    assert Change("line1", "case") in r.changes


def test_directional_post_rules() -> None:
    # Pre-directional abbreviation only with >=3 street words
    r = normalize(Address(line1="123 North St", country="US"))
    assert r.address.line1 == "123 NORTH ST"  # NORTH not abbreviated

    r = normalize(Address(line1="123 North Main Street", country="US"))
    assert r.address.line1 == "123 N MAIN ST"
    assert Change("line1", "directional") in r.changes

    # Post-directional: '123 Main Street North' should not abbreviate North
    # because it is adjacent to suffix (our rule).
    r = normalize(Address(line1="123 Main Street North", country="US"))
    assert r.address.line1 == "123 MAIN ST NORTH"

    # Post-directional with separation: '123 Main Street East North' (nonsensical but tests rule)
    # Not reliable; we skip.


def test_unit_designator_no_identifier() -> None:
    # 'Suite' without identifier should remain as text
    r = normalize(Address(line1="123 Main St Suite", country="US"))
    assert r.address.line1 == "123 MAIN ST SUITE"
    assert Change("line1", "unit") not in r.changes


def test_punctuation_removal_exceptions() -> None:
    # Allowed: '#', '-', '/'
    r = normalize(Address(line1="123 Main St. #4-A/B", country="US"))
    # Period removed, other allowed punctuation kept
    assert r.address.line1 == "123 MAIN ST # 4-A/B"
    assert Change("line1", "punctuation") in r.changes


def test_zip_plus_4_with_space() -> None:
    r = normalize(Address(line1="123 Main St", postal_code="12345 6789", country="US"))
    assert r.address.postal_code == "12345-6789"
    assert Change("postal_code", "postal_code") in r.changes


def test_logger_has_null_handler() -> None:
    import logging

    from address_normalizer import logger

    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)
