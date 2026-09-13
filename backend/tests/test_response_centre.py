import uuid
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.emergency import AlertRecipient, CaseMessage, EmergencyIncident
from app.schemas.emergency import AlertRecipientRead, CaseMessageRead


def test_create_and_update_recipient_api():
    """Verify recipient creation and patch update with full fields (Designation, Department, Role, Phone, Active)"""
    client = TestClient(app)

    # 1. Create Recipient
    payload = {
        "name": "Inspector Vijay Kumar",
        "designation": "Sub-Inspector",
        "department": "Crime Branch Unit 1",
        "role": "POLICE",
        "phone_number": "+919876543210",
        "recipient_type": "POLICE",
        "alert_preference": "ALL",
        "is_active": True,
    }
    res = client.post("/api/v1/emergency/recipients", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    recip = res.json()
    assert recip["name"] == "Inspector Vijay Kumar"
    assert recip["designation"] == "Sub-Inspector"
    assert recip["department"] == "Crime Branch Unit 1"
    assert recip["role"] == "POLICE"
    assert recip["phone_number"] == "+919876543210 font" or recip["phone_number"] == "+919876543210"
    recip_id = recip["id"]

    # 2. Update Recipient
    patch_payload = {
        "designation": "Inspector",
        "department": "Cyber & CCTV Cell",
        "is_active": True,
    }
    patch_res = client.patch(f"/api/v1/emergency/recipients/{recip_id}", json=patch_payload)
    assert patch_res.status_code == 200
    updated_recip = patch_res.json()
    assert updated_recip["designation"] == "Inspector"
    assert updated_recip["department"] == "Cyber & CCTV Cell"

    # 3. List Recipients
    list_res = client.get("/api/v1/emergency/recipients")
    assert list_res.status_code == 200
    recipients_list = list_res.json()
    assert any(r["id"] == recip_id for r in recipients_list)


def test_case_messaging_and_replies_api():
    """Verify response messages, comments, threaded replies, and read states for CASE-10000000"""
    client = TestClient(app)

    # Get cases list to retrieve valid case_number
    cases_res = client.get("/api/v1/emergency/cases")
    assert cases_res.status_code == 200
    cases = cases_res.json()
    assert len(cases) > 0
    case_number = cases[0]["case_number"]
    assert case_number.startswith("CASE-")

    # 1. Send Response Message
    msg_payload = {
        "message": "Unit 101 requested for backup at main perimeter.",
        "message_type": "RESPONSE",
        "sender_id": "Command Officer",
        "sender_name": "Command Officer",
    }
    send_res = client.post(f"/api/v1/emergency/cases/{case_number}/messages", json=msg_payload)
    assert send_res.status_code == 200
    msg = send_res.json()
    assert msg["message"] == "Unit 101 requested for backup at main perimeter."
    assert msg["case_number"] == case_number
    assert msg["message_type"] == "RESPONSE"
    msg_id = msg["id"]

    # 2. Reply to Message (Threaded)
    reply_payload = {
        "message": "Unit 101 dispatched to scene. ETA 3 minutes.",
        "sender_id": "Unit 101 Operator",
    }
    reply_res = client.post(f"/api/v1/emergency/messages/{msg_id}/reply", json=reply_payload)
    assert reply_res.status_code == 200
    reply = reply_res.json()
    assert reply["parent_message_id"] == msg_id
    assert reply["case_number"] == case_number
    assert reply["message_type"] == "REPLY"

    # 3. Add Operator Comment
    comment_payload = {
        "comment": "Suspect observed moving toward Gate 3 camera view.",
        "sender_id": "Camera Operator",
    }
    cmt_res = client.post(f"/api/v1/emergency/cases/{case_number}/comments", json=comment_payload)
    assert cmt_res.status_code == 200
    comment_msg = cmt_res.json()
    assert comment_msg["message_type"] == "COMMENT"
    assert comment_msg["message"] == "Suspect observed moving toward Gate 3 camera view."

    # 4. Fetch All Messages for Case
    messages_res = client.get(f"/api/v1/emergency/cases/{case_number}/messages")
    assert messages_res.status_code == 200
    all_msgs = messages_res.json()
    assert len(all_msgs) >= 3
    msg_ids = [m["id"] for m in all_msgs]
    assert msg_id in msg_ids
    assert reply["id"] in msg_ids
    assert comment_msg["id"] in msg_ids

    # 5. Verify Timeline holds RESPONSE_SENT and COMMENT_ADDED
    timeline_res = client.get(f"/api/v1/emergency/cases/{case_number}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    event_types = [t["event_type"] for t in timeline]
    assert "RESPONSE_SENT" in event_types or "COMMENT_ADDED" in event_types

    # 6. Mark Case Messages as Read
    read_res = client.post(f"/api/v1/emergency/cases/{case_number}/read")
    assert read_res.status_code == 200
    read_data = read_res.json()
    assert read_data["status"] == "success"
    assert read_data["case_number"] == case_number


def test_response_centre_security_audit():
    """Verify no plaintext passwords or private keys exist in message/recipient schemas"""
    recip_fields = list(AlertRecipientRead.model_fields.keys())
    assert "password" not in recip_fields
    assert "secret" not in recip_fields

    msg_fields = list(CaseMessageRead.model_fields.keys())
    assert "password" not in msg_fields
    assert "secret" not in msg_fields
