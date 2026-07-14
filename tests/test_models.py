import unittest

from inspection_ripper.models import (
    DamageCategory,
    InspectionFindings,
    PropertyInfo,
    get_field_completeness,
)

def test_property_info_defaults():
    p = PropertyInfo()
    assert p.address == ""
    assert p.bedrooms == 0
    assert p.year_built == 0

def test_inspection_findings_defaults():
    f = InspectionFindings()
    assert f.foundation == []
    assert f.overall_condition == ""

def test_get_field_completeness_empty():
    findings = InspectionFindings()
    c = get_field_completeness(findings)
    assert c.address_found is False
    assert c.foundation_found is False

def test_get_field_completeness_populated():
    findings = InspectionFindings(
        property=PropertyInfo(
            address="123 Main Street",
            bedrooms=2,
            bathrooms=3,
            square_footage=1500,
            year_built=1990,
        ),
        overall_condition="fair",
        foundation=[
            DamageCategory(category="foundation", severity="high", description="Crack in wall", page_number=4)
        ],
    )
    c = get_field_completeness(findings)
    assert c.address_found is True
    assert c.bedrooms_found is True
    assert c.foundation_found is True
    assert c.roof_found is False

def test_damage_category_fields():
    d = DamageCategory(
        category="roof",
        severity="critical",
        description="Missing shingles",
        page_number=12,
        requires_sub_report=True,
    )
    assert d.category == "roof"
    assert d.severity == "critical"
    assert d.requires_sub_report is True


def test_inspection_findings_json_round_trip():
      findings = InspectionFindings(
          property=PropertyInfo(address="456 Oak Ave"),
          overall_condition="poor",
      )
      json_str = findings.model_dump_json()
      restored = InspectionFindings.model_validate_json(json_str)
      assert restored.property.address == "456 Oak Ave"
      assert restored.overall_condition == "poor"






if __name__ == '__main__':
    unittest.main()
