import unittest
import json

from inspection_ripper.client import GrokClient
from inspection_ripper.extractor import Extractor
from inspection_ripper.models import AgentResult, InspectionFindings


def make_extractor():
    client = GrokClient(api_key="test-key")
    return Extractor(client=client)


def test_extract_demographics_populates_property():
    extractor = make_extractor()
    findings = InspectionFindings()
    data = {
        "property": {
            "address": "123 Main St",
            "bedrooms": 4,
            "bathrooms": 2,
            "square_footage": 2000,
            "year_built": 1985,
        },
        "overall_condition": "fair",
        "notes": "Older home, well maintained.",
    }
    extractor._extract_demographics(data, findings)
    assert findings.property.address == "123 Main St"
    assert findings.property.bedrooms == 4
    assert findings.overall_condition == "fair"
    assert findings.notes == "Older home, well maintained."


def test_extract_demographics_missing_fields():
    extractor = make_extractor()
    findings = InspectionFindings()
    extractor._extract_demographics({}, findings)
    assert findings.property.address == ""
    assert findings.property.bedrooms == 0


def test_extract_damage_appends_to_correct_list():
    extractor = make_extractor()
    findings = InspectionFindings()
    data = {
        "foundation": [{"severity": "high", "description": "Crack", "page_number": 3, "requires_sub_report": False}],
        "roof": [
            {"severity": "medium", "description": "Missing shingles", "page_number": 7, "requires_sub_report": False}],
        "hvac": [], "electrical": [], "plumbing": [], "other": [],
    }
    extractor._extract_damage(data, findings)
    assert len(findings.foundation) == 1
    assert findings.foundation[0].severity == "high"
    assert len(findings.roof) == 1
    assert findings.roof[0].description == "Missing shingles"
    assert len(findings.hvac) == 0


def test_extract_damage_requires_sub_report():
    extractor = make_extractor()
    findings = InspectionFindings()
    data = {
        "foundation": [], "roof": [], "hvac": [],
        "electrical": [
            {"severity": "critical", "description": "Panel issue", "page_number": 10, "requires_sub_report": True}],
        "plumbing": [], "other": [],
    }
    extractor._extract_damage(data, findings)
    assert findings.electrical[0].requires_sub_report is True


def test_combine_results_routes_by_agent_name():
    extractor = make_extractor()
    demo_data = {
        "property": {"address": "789 Elm St", "bedrooms": 3, "bathrooms": 1, "square_footage": 1200,
                     "year_built": 2001},
        "overall_condition": "good",
        "notes": "",
    }
    damage_data = {
        "foundation": [], "hvac": [], "electrical": [], "plumbing": [], "other": [],
        "roof": [{"severity": "low", "description": "Minor wear", "page_number": 5, "requires_sub_report": False}],
    }
    results = [
        AgentResult(agent_name="demographics", success=True, result=json.dumps(demo_data)),
        AgentResult(agent_name="damage", success=True, result=json.dumps(damage_data)),
    ]
    findings = extractor._combine_results(results)
    assert findings.property.address == "789 Elm St"
    assert len(findings.roof) == 1


def test_combine_results_skips_failed_agents():
    extractor = make_extractor()
    results = [
        AgentResult(agent_name="demographics", success=False, error_message="timeout"),
        AgentResult(agent_name="damage", success=False, error_message="timeout"),
    ]
    findings = extractor._combine_results(results)
    assert findings.property.address == ""
    assert findings.foundation == []


def test_combine_results_skips_invalid_json():
    extractor = make_extractor()
    results = [
        AgentResult(agent_name="demographics", success=True, result="not valid json {{"),
    ]
    findings = extractor._combine_results(results)
    assert findings.property.address == ""


if __name__ == '__main__':
    unittest.main()
