from typing import TypedDict

class Incident(TypedDict):
    report: str
    category: str
    category_justification: str
    critical: bool
    scope: str
    afected_systems: str
    responsible_person: str
    contact_info: str
    alert_draft: str
    report_template: str
    #structured_log_: str
