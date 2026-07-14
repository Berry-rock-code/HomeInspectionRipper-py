from .models import AgentExtractor


def get_demographics_prompt() -> str:
    return """\
Extract property demographics from this home inspection report:
- Address
- Number of bedrooms
- Number of bathrooms
- Square footage
- Year built
- Overall condition (good, fair, poor, critical)
- General notes

Return ONLY valid JSON with no additional text:
{
  "property": {
    "address": "string",
    "bedrooms": number,
    "bathrooms": number,
    "square_footage": number,
    "year_built": number
  },
  "overall_condition": "string",
  "notes": "string"
}"""


def get_damage_prompt() -> str:
    return """\
Extract and summarize damage and issues from this home inspection report, organized by category.

Rules:
- Group related issues into a single entry (e.g. multiple crawlspace column problems → one entry)
- Aim for 2-4 entries per category maximum; combine minor items where it makes sense
- Use the HIGHEST severity among the grouped issues for each entry
- Write descriptions as a concise summary (1-2 sentences), not a list of every instance
- Include the page number where the issue is first mentioned or shown
- Set requires_sub_report true only if the report explicitly calls for a specialist

Categories:
- foundation: cracks, settling, movement, crawlspace issues, support columns
- roof: shingles, flashing, gutters, drainage
- hvac: heating, cooling, ductwork, ventilation
- electrical: wiring, panel, outlets, GFCI, grounding
- plumbing: pipes, fixtures, water heater, drainage
- other: moisture, mold, insulation, windows, doors, siding, structural, pest, unpermitted work

Return ONLY valid JSON with no additional text:
{
  "foundation": [{"severity": "string", "description": "string", "page_number": number, "requires_sub_report": boolean}],
  "roof":       [{"severity": "string", "description": "string", "page_number": number, "requires_sub_report": boolean}],
  "hvac":       [{"severity": "string", "description": "string", "page_number": number, "requires_sub_report": boolean}],
  "electrical": [{"severity": "string", "description": "string", "page_number": number, "requires_sub_report": boolean}],
  "plumbing":   [{"severity": "string", "description": "string", "page_number": number, "requires_sub_report": boolean}],
  "other":      [{"severity": "string", "description": "string", "page_number": number, "requires_sub_report": boolean}]
}"""


def build_agents() -> list[AgentExtractor]:
    return [
        AgentExtractor(name="demographics", prompt=get_demographics_prompt(), timeout=120),
        AgentExtractor(name="damage", prompt=get_damage_prompt(), timeout=120),
    ]
