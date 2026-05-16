from typing import TypedDict

class Incident(TypedDict):
    id: str
    timestamp: str
    report_text: str
    category: str
    category_justification: str
    critical: bool
    scope: str
    affected_systems: str
    responsible_person: str
    contact_info: str
    alert_draft: str
    report_template: str
    #structured_log_: str
