from app.services.governance import compare_baseline_snapshots


def test_baseline_comparison_identifies_all_change_types() -> None:
    baseline = [
        {
            "code": "REQ-0001",
            "title": "Login",
            "description": "The system shall allow login.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "approved",
            "version": 1,
        },
        {
            "code": "REQ-0002",
            "title": "Export",
            "description": "The system shall export reports.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "approved",
            "version": 1,
        },
        {
            "code": "REQ-0003",
            "title": "Removed",
            "description": "This requirement will be removed.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "approved",
            "version": 1,
        },
    ]
    current = [
        baseline[0],
        {
            **baseline[1],
            "description": "The system shall export PDF and CSV reports.",
            "version": 2,
        },
        {
            "code": "REQ-0004",
            "title": "Audit",
            "description": "The system shall retain an audit log.",
            "requirement_type": "functional",
            "non_functional_category": None,
            "status": "draft",
            "version": 1,
        },
    ]

    comparison = compare_baseline_snapshots(baseline, current)

    assert comparison["unchanged"] == ["REQ-0001"]
    assert comparison["modified"][0]["code"] == "REQ-0002"
    assert comparison["modified"][0]["changed_fields"] == ["description", "version"]
    assert comparison["removed"][0]["code"] == "REQ-0003"
    assert comparison["added"][0]["code"] == "REQ-0004"
