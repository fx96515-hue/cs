"""Tests for reports API routes."""

from app.models.report import Report
from datetime import datetime, timezone


def test_list_reports_empty(client, auth_headers, db):
    """Test listing reports when none exist."""
    response = client.get("/reports", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_reports_with_data(client, auth_headers, db):
    """Test listing reports with existing data."""
    report1 = Report(
        report_at=datetime.now(timezone.utc), kind="daily", markdown="# Test Report 1"
    )
    report2 = Report(
        report_at=datetime.now(timezone.utc), kind="daily", markdown="# Test Report 2"
    )
    db.add_all([report1, report2])
    db.commit()

    response = client.get("/reports", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_report_by_id(client, auth_headers, db):
    """Test getting a specific report by ID."""
    report = Report(
        report_at=datetime.now(timezone.utc), kind="daily", markdown="# Test Report"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    response = client.get(f"/reports/{report.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report.id
    assert data["kind"] == "daily"


def test_get_report_not_found(client, auth_headers, db):
    """Test getting a non-existent report."""
    response = client.get("/reports/99999", headers=auth_headers)

    assert response.status_code == 404


def test_list_reports_with_limit(client, auth_headers, db):
    """Test listing reports with limit parameter."""
    for i in range(5):
        report = Report(
            report_at=datetime.now(timezone.utc), kind="daily", markdown=f"# Report {i}"
        )
        db.add(report)
    db.commit()

    response = client.get("/reports?limit=3", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3


def test_viewer_can_read_reports(client, viewer_auth_headers, db):
    """Test that viewers can read reports."""
    report = Report(
        report_at=datetime.now(timezone.utc), kind="daily", markdown="# Test Report"
    )
    db.add(report)
    db.commit()

    response = client.get("/reports", headers=viewer_auth_headers)

    assert response.status_code == 200


def test_reports_without_auth(client, db):
    """Test accessing reports without authentication."""
    response = client.get("/reports")

    assert response.status_code == 401
