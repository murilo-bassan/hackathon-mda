from typing import List, TypedDict

class Incident(TypedDict):
    id: str
    timestamp: str
    free_text: str
    category: str
    category_justification: str
    critical: bool
    critical_justification: str
    scope: str
    affected_systems: str
    responsible_person: str
    contact_info: str
    containment_steps: List[str]
    containment_justification: str
    alert_draft: str
    report_template: str
    validation_status: bool
