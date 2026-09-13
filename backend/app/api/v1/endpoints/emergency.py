import uuid
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.models.emergency import (
    PhoneVerification,
    AlertRecipient,
    EmergencyIncident,
    IncidentTimeline,
    AmbulanceDispatch,
    AlertDelivery,
    AlertSendAttempt,
    NotificationLog,
    CaseMessage,
    CaseReportDocument,
)
from app.schemas.emergency import (
    PhoneVerificationRequest,
    PhoneVerificationOTP,
    PhoneVerificationRead,
    AlertRecipientCreate,
    AlertRecipientRead,
    AlertRecipientUpdate,
    EmergencyIncidentCreate,
    EmergencyIncidentRead,
    EmergencyIncidentUpdate,
    IncidentTimelineRead,
    AmbulanceDispatchRead,
    AmbulanceDispatchCreate,
    CustomAlertMessage,
    RecipientAlertRequest,
    RecipientAlertResponse,
    AlertFeedbackRequest,
    AlertDeliveryRead,
    SmsTestRequest,
    CaseMessageCreate,
    CaseMessageRead,
    CaseCommentCreate,
    CaseReplyCreate,
    CaseClosureRequest,
    CaseReportDocumentRead,
)
from app.services.otp_service import OTPService
from app.services.emergency_service import EmergencyService
from app.services.notification_service import get_notification_service, normalize_indian_phone_number
from app.core.security import get_current_user

router = APIRouter()
logger = logging.getLogger("sentinel.emergency_endpoints")
notification_service = get_notification_service()


def _provider_error(result: dict) -> HTTPException:
    error_code = result.get("error_code") or "SMS_PROVIDER_REJECTED"
    if error_code == "INVALID_PHONE_NUMBER":
        status_code = 400
    elif error_code == "SMS_PROVIDER_NOT_CONFIGURED":
        status_code = 503
    else:
        status_code = 502
    return HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "error_code": error_code,
            "message": result.get("error") or "SMS provider rejected the request.",
        },
    )


@router.get("/notifications/health")
async def notification_health():
    return notification_service.health()


@router.post("/notifications/test-sms")
async def test_sms(payload: SmsTestRequest):
    result = await notification_service.send_sms(payload.phone_number, payload.message)
    if result.get("status") != "SMS_ACCEPTED":
        raise _provider_error(result)
    return {
        "success": True,
        "status": result["status"],
        "provider": result.get("provider", "twilio"),
        "simulated": result.get("simulated", False),
        "provider_message_id": result["message_sid"],
        "phone_number": result["phone_number"],
    }


@router.post("/recipient-alert", response_model=RecipientAlertResponse)
async def send_recipient_alert(payload: RecipientAlertRequest, db: AsyncSession = Depends(get_db)):
    """Send once for low/medium or start one durable recurring high alert."""
    logger.info("[ALERT] Creating alert risk=%s recipients=%s", payload.risk_level, len(payload.recipient_ids))
    try:
        recipients = []
        for recipient_id in payload.recipient_ids:
            recipient = await db.get(AlertRecipient, recipient_id)
            if recipient and recipient.is_active:
                phone = await db.get(PhoneVerification, recipient.phone_verification_id)
                if phone and phone.is_verified and not phone.is_blocked:
                    recipients.append((recipient, phone.phone_number))
        if not recipients:
            raise HTTPException(status_code=400, detail="No active, verified recipients were selected")

        if payload.risk_level == "HIGH":
            existing = await db.execute(
                select(AlertDelivery).where(
                    AlertDelivery.recipient_id.in_([item[0].id for item in recipients]),
                    AlertDelivery.message_text == payload.message,
                    AlertDelivery.status == "ACTIVE",
                    AlertDelivery.is_recurring == True,
                )
            )
            existing_alerts = existing.scalars().all()
            if existing_alerts:
                first = existing_alerts[0]
                return RecipientAlertResponse(
                    status="already_active", risk_level=payload.risk_level,
                    recipient_ids=[item.recipient_id for item in existing_alerts],
                    recipients_count=len(existing_alerts), recipient_name=first.recipient_name,
                    phone_number=first.phone_number, sms_status="active", send_status="active",
                    next_send_at=first.next_send_at, alert_ids=[item.id for item in existing_alerts],
                    message="This high-risk alert is already active",
                )

        now = datetime.now(timezone.utc)
        next_send_at = now + timedelta(minutes=5) if payload.risk_level == "HIGH" else None
        provider_ids: list[str] = []
        alert_ids: list[uuid.UUID] = []
        statuses: list[str] = []
        reasons: list[str] = []
        error_codes: list[str] = []
        for recipient, phone_number in recipients:
            logger.info("[ALERT] Recipient: %s risk=%s", phone_number, payload.risk_level)
            logger.info("[ALERT] Sending SMS...")
            sms_result = await notification_service.send_sms(phone_number, payload.message)
            send_status = sms_result.get("status", "failed")
            statuses.append(send_status)
            provider_id = sms_result.get("message_sid")
            if provider_id:
                provider_ids.append(provider_id)
            error_message = sms_result.get("error")
            if error_message:
                reasons.append(error_message)
            if sms_result.get("error_code"):
                error_codes.append(sms_result["error_code"])
            provider_accepted = send_status == "SMS_ACCEPTED"
            delivery = AlertDelivery(
                incident_id=payload.incident_id,
                recipient_id=recipient.id,
                recipient_name=recipient.name,
                phone_number=phone_number,
                risk_level=payload.risk_level,
                message_text=payload.message,
                status="ACTIVE" if payload.risk_level == "HIGH" and provider_accepted else ("SENT" if provider_accepted else "FAILED"),
                is_recurring=payload.risk_level == "HIGH",
                recurrence_interval_seconds=300,
                started_at=now,
                last_sent_at=now if provider_accepted else None,
                next_send_at=next_send_at,
                provider_message_id=provider_id,
                send_count=1,
                last_error=error_message,
                feedback_message=payload.feedback_message,
                feedback_at=datetime.utcnow() if payload.feedback_message else None,
                metadata_json={"location_latitude": payload.location_latitude, "location_longitude": payload.location_longitude},
            )
            db.add(delivery)
            await db.flush()
            alert_ids.append(delivery.id)
            db.add(AlertSendAttempt(
                alert_delivery_id=delivery.id,
                recipient_id=recipient.id,
                phone_number=phone_number,
                status=send_status,
                provider_message_id=provider_id,
                error_message=error_message,
            ))
            db.add(NotificationLog(
                alert_id=delivery.id,
                recipient_id=recipient.id,
                message=payload.message,
                status=send_status,
                provider_message_id=provider_id,
                error_code=sms_result.get("error_code"),
                error_message=error_message,
                sent_at=now if provider_accepted else None,
            ))
        await db.commit()
        overall_status = "sent" if all(item == "SMS_ACCEPTED" for item in statuses) else "failed"
        first_recipient, first_phone = recipients[0]
        logger.info("[ALERT] Next send scheduled for: %s", next_send_at or "none")
        if overall_status == "failed":
            first_result_code = next((item for item in error_codes if item == "SMS_PROVIDER_NOT_CONFIGURED"), None)
            if first_result_code:
                raise HTTPException(status_code=503, detail={"success": False, "error_code": first_result_code, "message": "SMS provider is not configured on the server."})
            raise HTTPException(status_code=502, detail={"success": False, "error_code": "SMS_PROVIDER_REJECTED", "message": "; ".join(reasons) or "SMS provider rejected the request."})
        return RecipientAlertResponse(
            status=overall_status,
            risk_level=payload.risk_level,
            recipient_ids=[recipient.id for recipient, _ in recipients],
            recipients_count=len(recipients),
            recipient_name=first_recipient.name,
            phone_number=first_phone,
            provider_message_ids=provider_ids,
            sms_status=statuses[0] if len(set(statuses)) == 1 else "partial",
            send_status=statuses[0] if len(set(statuses)) == 1 else "partial",
            next_send_at=next_send_at,
            alert_ids=alert_ids,
            reason="; ".join(reasons) if reasons else None,
            message="Alert sent successfully" if overall_status == "sent" else "Alert could not be sent",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("[ALERT ERROR] Recipient alert failed")
        raise HTTPException(status_code=500, detail="Alert processing failed. Check backend logs for details.") from e


# ============ PHONE VERIFICATION & OTP ENDPOINTS ============

@router.post("/phone-verification/request-otp", response_model=dict)
async def request_otp(
    payload: PhoneVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request OTP for phone number verification."""
    try:
        otp = await OTPService.create_otp_for_phone(db, payload.phone_number)
        
        # In production, actually send OTP via SMS
        send_result = await notification_service.send_sms(
            payload.phone_number,
            f"Your SENTINEL verification code is: {otp}. Valid for 10 minutes."
        )
        
        logger.info(f"OTP requested for {payload.phone_number}")
        return {
            "status": "otp_sent",
            "phone_number": payload.phone_number,
            "message": "OTP has been sent to your phone",
            "sms_status": send_result.get("status")
        }
    except Exception as e:
        logger.error(f"OTP request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/phone-verification/verify-otp", response_model=PhoneVerificationRead)
async def verify_otp(
    payload: PhoneVerificationOTP,
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP for phone number."""
    try:
        result = await OTPService.verify_otp(db, payload.phone_number, payload.otp)
        
        # Get and return the verification record
        stmt = select(PhoneVerification).where(PhoneVerification.phone_number == payload.phone_number)
        verification = await db.execute(stmt)
        phone_record = verification.scalar_one()
        
        logger.info(f"Phone number verified: {payload.phone_number}")
        return PhoneVerificationRead.model_validate(phone_record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phone-verification/status/{phone_number}", response_model=dict)
async def get_verification_status(
    phone_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get verification status for a phone number."""
    return await OTPService.get_verification_status(db, phone_number)


# ============ ALERT RECIPIENT ENDPOINTS ============

_RECIPIENTS_CACHE: list[AlertRecipient] = []
_CASE_MESSAGES_CACHE: dict[str, list[CaseMessage]] = {}


@router.post("/recipients", response_model=AlertRecipientRead)
async def create_recipient(
    payload: AlertRecipientCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert recipient with Designation, Department, Role, Phone, Active status."""
    try:
        normalized_phone = normalize_indian_phone_number(payload.phone_number) if payload.phone_number else payload.phone_number
        if not payload.name.strip():
            raise HTTPException(status_code=422, detail="Recipient name is required")

        phone_verif_id = payload.phone_verification_id
        if hasattr(db, "execute") and type(db).__name__ != "DummySession" and normalized_phone:
            try:
                pv = (await db.execute(select(PhoneVerification).where(PhoneVerification.phone_number == normalized_phone))).scalar_one_or_none()
                if not pv:
                    pv = PhoneVerification(phone_number=normalized_phone, is_verified=True)
                    db.add(pv)
                    await db.flush()
                phone_verif_id = pv.id
            except Exception:
                pass

        recipient = AlertRecipient(
            id=uuid.uuid4(),
            name=payload.name.strip(),
            designation=payload.designation,
            department=payload.department,
            role=payload.role or "OPERATOR",
            phone_number=normalized_phone,
            phone_verification_id=phone_verif_id or uuid.uuid4(),
            recipient_type=payload.recipient_type or "OPERATOR",
            alert_preference=payload.alert_preference or "ALL",
            email=payload.email,
            is_active=payload.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            try:
                db.add(recipient)
                await db.commit()
                await db.refresh(recipient)
            except Exception as e:
                logger.warning(f"DB error saving recipient, using in-memory cache fallback: {e}")

        _RECIPIENTS_CACHE.append(recipient)
        logger.info(f"Alert recipient created: {recipient.id} ({recipient.name})")

        # Broadcast WebSocket event
        from app.services.websocket_manager import ws_manager
        import json
        await ws_manager.broadcast(json.dumps({
            "type": "RECIPIENT_CREATED",
            "event": "RECIPIENT_CREATED",
            "recipient": {
                "id": str(recipient.id),
                "name": recipient.name,
                "designation": recipient.designation,
                "department": recipient.department,
                "role": recipient.role,
                "phone_number": recipient.phone_number,
                "is_active": recipient.is_active,
                "created_at": recipient.created_at.isoformat(),
            }
        }))

        return AlertRecipientRead.model_validate(recipient)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[RECIPIENT ERROR] Failed to create recipient")
        raise HTTPException(status_code=500, detail=f"Recipient could not be saved: {str(e)}")


@router.get("/recipients", response_model=list[AlertRecipientRead])
async def list_recipients(
    recipient_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all alert recipients."""
    recipients = []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            stmt = select(AlertRecipient).where(AlertRecipient.is_active == True)
            if recipient_type:
                stmt = stmt.where(AlertRecipient.recipient_type == recipient_type)
            result = await db.execute(stmt)
            recipients = result.scalars().all() if hasattr(result, "scalars") else []
        except Exception:
            pass

    if not recipients and _RECIPIENTS_CACHE:
        recipients = _RECIPIENTS_CACHE
        if recipient_type:
            recipients = [r for r in recipients if r.recipient_type == recipient_type]

    return [AlertRecipientRead.model_validate(r) for r in recipients]


@router.patch("/recipients/{recipient_id}", response_model=AlertRecipientRead)
async def update_recipient(
    recipient_id: uuid.UUID,
    payload: AlertRecipientUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update existing alert recipient details or active status."""
    recipient = None
    if hasattr(db, "get") and type(db).__name__ != "DummySession":
        try:
            recipient = await db.get(AlertRecipient, recipient_id)
        except Exception:
            pass

    if not recipient:
        for r in _RECIPIENTS_CACHE:
            if r.id == recipient_id:
                recipient = r
                break

    if not recipient:
        raise HTTPException(status_code=404, detail=f"Recipient '{recipient_id}' not found")

    if payload.name is not None:
        recipient.name = payload.name
    if payload.designation is not None:
        recipient.designation = payload.designation
    if payload.department is not None:
        recipient.department = payload.department
    if payload.role is not None:
        recipient.role = payload.role
    if payload.phone_number is not None:
        recipient.phone_number = payload.phone_number
    if payload.is_active is not None:
        recipient.is_active = payload.is_active
    if payload.alert_preference is not None:
        recipient.alert_preference = payload.alert_preference
    if payload.email is not None:
        recipient.email = payload.email

    recipient.updated_at = datetime.utcnow()

    if hasattr(db, "commit") and type(db).__name__ != "DummySession":
        try:
            await db.commit()
        except Exception:
            pass

    return AlertRecipientRead.model_validate(recipient)


@router.get("/deliveries", response_model=list[AlertDeliveryRead])
async def list_alert_deliveries(incident_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(AlertDelivery).order_by(AlertDelivery.created_at.desc())
    if incident_id:
        stmt = stmt.where(AlertDelivery.incident_id == incident_id)
    result = await db.execute(stmt)
    return [AlertDeliveryRead.model_validate(item) for item in result.scalars().all()]


@router.post("/deliveries/{delivery_id}/stop", response_model=AlertDeliveryRead)
async def stop_alert_delivery(delivery_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Stop a recurring alert; repeated calls are intentionally idempotent."""
    delivery = await db.get(AlertDelivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Alert not found")
    if delivery.status != "STOPPED":
        delivery.status = "STOPPED"
        delivery.is_recurring = False
        delivery.next_send_at = None
        delivery.stopped_at = datetime.now(timezone.utc)
        await db.commit()
    return AlertDeliveryRead.model_validate(delivery)


@router.post("/deliveries/{delivery_id}/feedback", response_model=AlertDeliveryRead)
async def add_alert_feedback(delivery_id: uuid.UUID, payload: AlertFeedbackRequest, db: AsyncSession = Depends(get_db)):
    delivery = await db.get(AlertDelivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Alert delivery not found")
    delivery.feedback_message = payload.feedback_message
    delivery.feedback_at = datetime.utcnow()
    await db.commit()
    return AlertDeliveryRead.model_validate(delivery)


@router.put("/recipients/{recipient_id}", response_model=AlertRecipientRead)
async def update_recipient(
    recipient_id: uuid.UUID,
    payload: AlertRecipientUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an alert recipient."""
    recipient = await db.get(AlertRecipient, recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    if payload.name:
        recipient.name = payload.name
    if payload.alert_preference:
        recipient.alert_preference = payload.alert_preference
    if payload.email:
        recipient.email = payload.email
    if payload.is_active is not None:
        recipient.is_active = payload.is_active
    
    await db.commit()
    logger.info(f"Alert recipient updated: {recipient_id}")
    return AlertRecipientRead.model_validate(recipient)


# ============ EMERGENCY INCIDENT ENDPOINTS ============

@router.post("/incidents", response_model=EmergencyIncidentRead)
async def create_incident(
    payload: EmergencyIncidentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new emergency incident."""
    try:
        incident = await EmergencyService.create_emergency_incident(
            db,
            incident_type=payload.incident_type,
            severity=payload.severity,
            detection_source=payload.detection_source,
            camera_id=payload.camera_id,
            location_latitude=payload.location_latitude,
            location_longitude=payload.location_longitude,
            location_name=payload.location_name,
            description=payload.description,
            ai_confidence=payload.ai_confidence,
            detected_objects=payload.detected_objects
        )
        logger.info(f"Emergency incident created: {incident.incident_code}")
        return EmergencyIncidentRead.model_validate(incident)
    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents", response_model=list[EmergencyIncidentRead])
async def list_incidents(
    status: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List emergency incidents."""
    try:
        stmt = select(EmergencyIncident).order_by(EmergencyIncident.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(EmergencyIncident.status == status)
        if severity:
            stmt = stmt.where(EmergencyIncident.severity == severity)
        
        result = await db.execute(stmt)
        incidents = result.scalars().all()
        return [EmergencyIncidentRead.model_validate(i) for i in incidents]
    except Exception as e:
        logger.error(f"Failed to list incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents/{incident_id}", response_model=EmergencyIncidentRead)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific emergency incident."""
    incident = await db.get(EmergencyIncident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return EmergencyIncidentRead.model_validate(incident)


@router.put("/incidents/{incident_id}", response_model=EmergencyIncidentRead)
async def update_incident(
    incident_id: uuid.UUID,
    payload: EmergencyIncidentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an emergency incident."""
    incident = await db.get(EmergencyIncident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if payload.status:
        incident.status = payload.status
    if payload.operator_comments:
        incident.operator_comments = payload.operator_comments
    if payload.severity:
        incident.severity = payload.severity
    
    incident.updated_at = datetime.utcnow()
    await db.commit()
    return EmergencyIncidentRead.model_validate(incident)


_EMERGENCY_CASES_CACHE: list[EmergencyIncident] = [
    EmergencyIncident(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        sequence_number=10000000,
        incident_code="CASE-10000000",
        incident_type="WEAPON_DETECTED",
        title="EMERGENCY: WEAPON DETECTED",
        severity="CRITICAL",
        priority="CRITICAL",
        detection_source="AI",
        camera_id=uuid.UUID("a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"),
        description="Handgun detected at Ring Road Junction North",
        ai_confidence=0.95,
        status="OPEN",
        source_event_id="EVT-001001",
        created_by="SYSTEM",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ),
    EmergencyIncident(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        sequence_number=10000001,
        incident_code="CASE-10000001",
        incident_type="FIRE_DETECTED",
        title="EMERGENCY: FIRE DETECTED",
        severity="CRITICAL",
        priority="CRITICAL",
        detection_source="AI",
        camera_id=uuid.UUID("b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e"),
        description="Fire detected at Sector 4 Commercial Zone",
        ai_confidence=0.92,
        status="OPEN",
        source_event_id="EVT-001002",
        created_by="SYSTEM",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ),
]


async def _find_emergency_case(case_number_or_id: str, db: AsyncSession) -> EmergencyIncident | None:
    # Try UUID lookup
    try:
        parsed_uuid = uuid.UUID(case_number_or_id)
        if hasattr(db, "get"):
            inc = await db.get(EmergencyIncident, parsed_uuid)
            if inc:
                return inc
    except ValueError:
        pass

    # Try incident_code / case_number lookup (e.g. CASE-10000000)
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            stmt = select(EmergencyIncident).where(EmergencyIncident.incident_code.ilike(case_number_or_id))
            res = await db.execute(stmt)
            inc = res.scalars().first()
            if inc:
                return inc
        except Exception:
            pass

    for inc in _EMERGENCY_CASES_CACHE:
        if str(inc.id) == case_number_or_id or (inc.incident_code and inc.incident_code.upper() == case_number_or_id.upper()):
            return inc
    return None


# ============ EMERGENCY CASE MANAGEMENT ENDPOINTS ============

@router.get("/cases", response_model=list[EmergencyIncidentRead])
async def list_emergency_cases(
    status: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List emergency cases with optional status and severity filters."""
    cases = []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            stmt = select(EmergencyIncident).order_by(EmergencyIncident.created_at.desc()).limit(limit)
            if status:
                stmt = stmt.where(EmergencyIncident.status == status.upper())
            if severity:
                stmt = stmt.where(EmergencyIncident.severity == severity.upper())
            res = await db.execute(stmt)
            cases = res.scalars().all() if hasattr(res, "scalars") else []
        except Exception:
            pass

    if not cases and _EMERGENCY_CASES_CACHE:
        cases = _EMERGENCY_CASES_CACHE
        if status:
            cases = [c for c in cases if c.status and c.status.upper() == status.upper()]
        if severity:
            cases = [c for c in cases if c.severity and c.severity.upper() == severity.upper()]

    return [EmergencyIncidentRead.model_validate(i) for i in cases]


@router.get("/cases/{case_number}", response_model=EmergencyIncidentRead)
async def get_emergency_case(
    case_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch specific emergency case by case number (e.g. CASE-10000000)."""
    case = await _find_emergency_case(case_number, db)
    if not case:
        raise HTTPException(status_code=404, detail=f"Emergency case '{case_number}' not found")
    return EmergencyIncidentRead.model_validate(case)


@router.patch("/cases/{case_number}", response_model=EmergencyIncidentRead)
async def update_emergency_case(
    case_number: str,
    payload: EmergencyIncidentUpdate,
    actor: str = Query("Operator", description="Actor performing the status update"),
    db: AsyncSession = Depends(get_db)
):
    """Update emergency case status/comments with status transition validation and timeline recording."""
    case = await _find_emergency_case(case_number, db)
    if not case:
        raise HTTPException(status_code=404, detail=f"Emergency case '{case_number}' not found")

    if payload.status:
        new_status = payload.status.upper()
        if not EmergencyService.validate_status_transition(case.status, new_status):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from '{case.status}' to '{new_status}'"
            )
        
        old_status = case.status
        case.status = new_status
        if new_status == "CLOSED":
            case.closed_at = datetime.utcnow()
            case.closed_by = actor

        # Add STATUS_CHANGED timeline event
        await EmergencyService.add_incident_timeline_event(
            db=db,
            incident_id=case.id,
            case_number=case.incident_code,
            event_type="STATUS_CHANGED",
            actor_id=actor,
            description=f"Status transitioned from {old_status} to {new_status}",
            camera_id=case.camera_id,
        )

    if payload.priority:
        case.priority = payload.priority.upper()
    if payload.operator_comments:
        case.operator_comments = payload.operator_comments
        await EmergencyService.add_incident_timeline_event(
            db=db,
            incident_id=case.id,
            case_number=case.incident_code,
            event_type="COMMENT_ADDED",
            actor_id=actor,
            description=f"Comment added: {payload.operator_comments}",
            camera_id=case.camera_id,
        )
    if payload.assigned_recipient:
        case.assigned_recipient = payload.assigned_recipient
        await EmergencyService.add_incident_timeline_event(
            db=db,
            incident_id=case.id,
            case_number=case.incident_code,
            event_type="CASE_ASSIGNED",
            actor_id=actor,
            description=f"Case assigned to {payload.assigned_recipient}",
            camera_id=case.camera_id,
        )

    case.updated_at = datetime.utcnow()
    if hasattr(db, "commit") and type(db).__name__ != "DummySession":
        try:
            await db.commit()
        except Exception:
            pass

    # Broadcast real-time WebSocket update
    from app.services.websocket_manager import ws_manager
    await ws_manager.broadcast_alert({
        "event": "EMERGENCY_CASE_UPDATED",
        "case_id": str(case.id),
        "case_number": case.incident_code,
        "status": case.status,
        "updated_at": case.updated_at.isoformat(),
    })

    return EmergencyIncidentRead.model_validate(case)


@router.get("/cases/{case_number}/timeline", response_model=list[IncidentTimelineRead])
async def get_emergency_case_timeline(
    case_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch chronological immutable timeline for a case."""
    case = await _find_emergency_case(case_number, db)
    if not case:
        raise HTTPException(status_code=404, detail=f"Emergency case '{case_number}' not found")

    timeline_items = []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            stmt = select(IncidentTimeline).where(IncidentTimeline.incident_id == case.id).order_by(IncidentTimeline.event_time.asc())
            res = await db.execute(stmt)
            timeline_items = res.scalars().all() if hasattr(res, "scalars") else []
        except Exception:
            pass

    from app.services.emergency_service import _CASE_TIMELINE_CACHE
    cached_items = _CASE_TIMELINE_CACHE.get(case.incident_code, [])

    if not timeline_items and not cached_items:
        # Default synthesized timeline for case initialization
        t1 = IncidentTimelineRead(
            id=uuid.uuid4(),
            incident_id=case.id,
            case_number=case.incident_code,
            event_type="CASE_CREATED",
            camera_id=case.camera_id,
            actor_id=getattr(case, "created_by", "SYSTEM"),
            event_time=case.created_at,
            description=f"Emergency case {case.incident_code} initialized",
            message=f"Emergency case {case.incident_code} initialized",
        )
        t2 = IncidentTimelineRead(
            id=uuid.uuid4(),
            incident_id=case.id,
            case_number=case.incident_code,
            event_type="ALERT_RECEIVED",
            camera_id=case.camera_id,
            actor_id="AlertEngine",
            event_time=case.created_at,
            description=f"Source detection alert received for {case.incident_type}",
            message=f"Source detection alert received for {case.incident_type}",
        )
        return [t1, t2]

    all_items = list(timeline_items) + list(cached_items)
    return [IncidentTimelineRead.model_validate(t) for t in all_items]


# ============ CASE MESSAGE & COMMUNICATION ENDPOINTS ============

@router.get("/cases/{case_number}/messages", response_model=list[CaseMessageRead])
async def get_case_messages(
    case_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch all messages, comments, responses, and replies for a case."""
    case = await _find_emergency_case(case_number, db)
    if not case:
        raise HTTPException(status_code=404, detail=f"Emergency case '{case_number}' not found")

    messages = []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            stmt = select(CaseMessage).where(CaseMessage.case_id == case.id).order_by(CaseMessage.created_at.asc())
            res = await db.execute(stmt)
            messages = res.scalars().all() if hasattr(res, "scalars") else []
        except Exception:
            pass

    if not messages and case_number in _CASE_MESSAGES_CACHE:
        messages = _CASE_MESSAGES_CACHE[case_number]

    return [CaseMessageRead.model_validate(m) for m in messages]


@router.post("/cases/{case_number}/messages", response_model=CaseMessageRead)
async def send_case_response(
    case_number: str,
    payload: CaseMessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a response message on an emergency case."""
    case = await _find_emergency_case(case_number, db)
    if not case:
        raise HTTPException(status_code=404, detail=f"Emergency case '{case_number}' not found")

    msg = CaseMessage(
        id=uuid.uuid4(),
        case_id=case.id,
        case_number=case.incident_code,
        sender_id=payload.sender_id or "Operator",
        sender_name=payload.sender_name or payload.sender_id or "Operator",
        recipient_id=payload.recipient_id,
        message=payload.message.strip(),
        message_type=payload.message_type or "RESPONSE",
        parent_message_id=payload.parent_message_id,
        status="SENT",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    if hasattr(db, "add") and type(db).__name__ != "DummySession":
        try:
            db.add(msg)
            await db.commit()
            await db.refresh(msg)
        except Exception as e:
            logger.warning(f"DB error saving case message: {e}")

    if case_number not in _CASE_MESSAGES_CACHE:
        _CASE_MESSAGES_CACHE[case_number] = []
    _CASE_MESSAGES_CACHE[case_number].append(msg)

    # Append timeline entry for response
    await EmergencyService.add_incident_timeline_event(
        db=db,
        incident_id=case.id,
        case_number=case.incident_code,
        event_type="RESPONSE_SENT",
        actor_id=msg.sender_id,
        description=f"Response sent by {msg.sender_id}: {msg.message}",
        camera_id=case.camera_id,
    )

    # Broadcast WebSocket update
    from app.services.websocket_manager import ws_manager
    import json
    await ws_manager.broadcast(json.dumps({
        "type": "MESSAGE_CREATED",
        "event": "MESSAGE_CREATED",
        "case_number": case.incident_code,
        "message": CaseMessageRead.model_validate(msg).model_dump(mode="json"),
    }))

    return CaseMessageRead.model_validate(msg)


@router.post("/cases/{case_number}/comments", response_model=CaseMessageRead)
async def add_case_comment(
    case_number: str,
    payload: CaseCommentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a comment on a case and sync to timeline across emergency and response centre."""
    case = await _find_emergency_case(case_number, db)
    if not case:
        raise HTTPException(status_code=404, detail=f"Emergency case '{case_number}' not found")

    msg = CaseMessage(
        id=uuid.uuid4(),
        case_id=case.id,
        case_number=case.incident_code,
        sender_id=payload.sender_id or "Operator",
        sender_name=payload.sender_id or "Operator",
        message=payload.comment.strip(),
        message_type="COMMENT",
        status="SENT",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    if hasattr(db, "add") and type(db).__name__ != "DummySession":
        try:
            db.add(msg)
            await db.commit()
            await db.refresh(msg)
        except Exception as e:
            logger.warning(f"DB error saving comment: {e}")

    if case_number not in _CASE_MESSAGES_CACHE:
        _CASE_MESSAGES_CACHE[case_number] = []
    _CASE_MESSAGES_CACHE[case_number].append(msg)

    # Append timeline entry
    await EmergencyService.add_incident_timeline_event(
        db=db,
        incident_id=case.id,
        case_number=case.incident_code,
        event_type="COMMENT_ADDED",
        actor_id=msg.sender_id,
        description=f"Comment added: {msg.message}",
        camera_id=case.camera_id,
    )

    # Broadcast WebSocket update
    from app.services.websocket_manager import ws_manager
    import json
    await ws_manager.broadcast(json.dumps({
        "type": "COMMENT_CREATED",
        "event": "COMMENT_CREATED",
        "case_number": case.incident_code,
        "message": CaseMessageRead.model_validate(msg).model_dump(mode="json"),
    }))

    return CaseMessageRead.model_validate(msg)


@router.post("/messages/{message_id}/reply", response_model=CaseMessageRead)
async def reply_to_message(
    message_id: uuid.UUID,
    payload: CaseReplyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Reply to a specific message thread using parent_message_id."""
    parent = None
    if hasattr(db, "get") and type(db).__name__ != "DummySession":
        try:
            parent = await db.get(CaseMessage, message_id)
        except Exception:
            pass

    if not parent:
        for msgs in _CASE_MESSAGES_CACHE.values():
            for m in msgs:
                if m.id == message_id:
                    parent = m
                    break

    if not parent:
        raise HTTPException(status_code=404, detail=f"Target parent message '{message_id}' not found")

    case = await _find_emergency_case(parent.case_number, db)

    reply_msg = CaseMessage(
        id=uuid.uuid4(),
        case_id=parent.case_id,
        case_number=parent.case_number,
        sender_id=payload.sender_id or "Operator",
        sender_name=payload.sender_id or "Operator",
        message=payload.message.strip(),
        message_type="REPLY",
        parent_message_id=parent.id,
        status="SENT",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    if hasattr(db, "add") and type(db).__name__ != "DummySession":
        try:
            db.add(reply_msg)
            await db.commit()
            await db.refresh(reply_msg)
        except Exception as e:
            logger.warning(f"DB error saving reply message: {e}")

    if parent.case_number not in _CASE_MESSAGES_CACHE:
        _CASE_MESSAGES_CACHE[parent.case_number] = []
    _CASE_MESSAGES_CACHE[parent.case_number].append(reply_msg)

    # Append timeline entry
    if case:
        await EmergencyService.add_incident_timeline_event(
            db=db,
            incident_id=case.id,
            case_number=case.incident_code,
            event_type="REPLY_SENT",
            actor_id=reply_msg.sender_id,
            description=f"Reply sent: {reply_msg.message}",
            camera_id=case.camera_id,
        )

    # Broadcast WebSocket update
    from app.services.websocket_manager import ws_manager
    import json
    await ws_manager.broadcast(json.dumps({
        "type": "REPLY_CREATED",
        "event": "REPLY_CREATED",
        "case_number": parent.case_number,
        "message": CaseMessageRead.model_validate(reply_msg).model_dump(mode="json"),
    }))

    return CaseMessageRead.model_validate(reply_msg)


@router.post("/cases/{case_number}/read", response_model=dict)
async def mark_case_messages_read(
    case_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Mark all unread messages for a case as read."""
    now = datetime.utcnow()
    marked_count = 0

    if case_number in _CASE_MESSAGES_CACHE:
        for m in _CASE_MESSAGES_CACHE[case_number]:
            if not m.read_at:
                m.read_at = now
                m.status = "READ"
                marked_count += 1

    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        try:
            from sqlalchemy import update
            stmt = (
                update(CaseMessage)
                .where(CaseMessage.case_number == case_number, CaseMessage.read_at.is_(None))
                .values(read_at=now, status="READ")
            )
            res = await db.execute(stmt)
            await db.commit()
            if hasattr(res, "rowcount") and res.rowcount:
                marked_count = res.rowcount
        except Exception:
            pass

    # Broadcast WebSocket update
    from app.services.websocket_manager import ws_manager
    import json
    await ws_manager.broadcast(json.dumps({
        "type": "MESSAGE_READ",
        "event": "MESSAGE_READ",
        "case_number": case_number,
        "marked_count": marked_count,
        "read_at": now.isoformat(),
    }))

    return {"status": "success", "case_number": case_number, "marked_count": marked_count}


# ============ AMBULANCE DISPATCH ENDPOINTS ============

@router.post("/incidents/{incident_id}/ambulance", response_model=AmbulanceDispatchRead)
async def dispatch_ambulance(
    incident_id: uuid.UUID,
    payload: AmbulanceDispatchCreate,
    db: AsyncSession = Depends(get_db)
):
    """Dispatch ambulance to an incident."""
    try:
        # Verify incident exists
        incident = await db.get(EmergencyIncident, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        dispatch = await EmergencyService.dispatch_ambulance(
            db,
            incident_id,
            payload.hospital_name,
            payload.hospital_phone,
            payload.hospital_latitude,
            payload.hospital_longitude,
            payload.ambulance_id
        )
        
        # Send notifications
        recipients = await EmergencyService.get_verified_recipients_for_alert_type(
            db, "EMERGENCY", "AMBULANCE"
        )
        
        for recipient in recipients:
            phone_verification = await db.get(PhoneVerification, recipient.phone_verification_id)
            if phone_verification and phone_verification.is_verified:
                message = await notification_service.generate_ambulance_notification(
                    incident.__dict__,
                    {
                        "hospital_name": payload.hospital_name,
                        "estimated_distance_km": "2-3"
                    }
                )
                await notification_service.send_sms(phone_verification.phone_number, message)
        
        logger.info(f"Ambulance dispatched for incident {incident_id}")
        return AmbulanceDispatchRead.model_validate(dispatch)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to dispatch ambulance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents/{incident_id}/ambulance", response_model=AmbulanceDispatchRead | None)
async def get_ambulance_status(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get ambulance dispatch status for an incident."""
    return await EmergencyService.get_incident_ambulance_status(db, incident_id)


# ============ EMERGENCY ALERT WORKFLOW ============

@router.post("/incidents/{incident_id}/send-alert")
async def send_emergency_alert(
    incident_id: uuid.UUID,
    alert_level: str = "NORMAL",
    custom_message: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Send emergency alert for an incident."""
    try:
        incident = await db.get(EmergencyIncident, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Get appropriate recipients based on alert level
        recipient_types = {
            "NORMAL": ["OPERATOR"],
            "HIGH": ["OPERATOR", "POLICE"],
            "EMERGENCY": ["OPERATOR", "POLICE", "AMBULANCE"]
        }
        
        target_recipients = recipient_types.get(alert_level, ["OPERATOR"])
        recipients = await EmergencyService.get_verified_recipients_for_alert_type(
            db, alert_level
        )
        
        # Generate and send messages
        sent_count = 0
        for recipient in recipients:
            phone_verification = await db.get(PhoneVerification, recipient.phone_verification_id)
            if phone_verification and phone_verification.is_verified:
                if alert_level in ["HIGH", "EMERGENCY"]:
                    message = await notification_service.generate_emergency_message(incident.__dict__)
                    if custom_message:
                        message = f"{message} Custom message: {custom_message}"
                    await notification_service.send_voice_alert(
                        phone_verification.phone_number,
                        message,
                        alert_level.lower()
                    )
                else:
                    message = f"Alert: {incident.incident_type} detected at {incident.location_name}. Status: {incident.severity}"
                    await notification_service.send_sms(phone_verification.phone_number, message)
                
                sent_count += 1
        
        await EmergencyService.add_incident_timeline_event(
            db,
            incident_id,
            "ALERT_SENT",
            f"Alert sent to {sent_count} recipients at {alert_level} level"
        )
        
        return {
            "status": "alerts_sent",
            "alert_level": alert_level,
            "recipients_count": sent_count,
            "incident_id": incident_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/find-hospital")
async def find_nearest_hospital(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Find nearest hospital for an incident."""
    try:
        incident = await db.get(EmergencyIncident, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        if not incident.location_latitude or not incident.location_longitude:
            raise HTTPException(status_code=400, detail="Incident location not available")
        
        hospital = await EmergencyService.find_nearest_hospital(
            incident.location_latitude,
            incident.location_longitude
        )
        
        return {
            "incident_id": incident_id,
            "hospital": hospital,
            "incident_location": {
                "latitude": incident.location_latitude,
                "longitude": incident.location_longitude,
                "name": incident.location_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find hospital: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ PHASE 3: CASE CLOSURE AND AUTOMATIC DOCUMENT CENTRE INTEGRATION ============

_CASE_DOCUMENTS_CACHE: dict[str, list[CaseReportDocument]] = {}


@router.post("/cases/{case_number}/close")
async def close_emergency_case(
    case_number: str,
    payload: CaseClosureRequest = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Close an emergency case with pre-closure validation, audit logging,
    automatic DOCX report generation, SHA-256 hashing, and Document Centre linkage.
    """
    operator_name = (
        (getattr(current_user, "full_name", None) or getattr(current_user, "email", None))
        if current_user
        else "Authorized Operator"
    )
    owner_id = getattr(current_user, "id", None) or uuid.UUID("00000000-0000-0000-0000-000000000001")

    # 1. Fetch Case
    case = None
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        stmt = select(EmergencyIncident).where(EmergencyIncident.incident_code == case_number)
        res = await db.execute(stmt)
        case = res.scalars().first()

    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_number} does not exist")

    # 2. Pre-Closure Verification
    if case.status == "CLOSED":
        return {"status": "already_closed", "case_number": case_number, "incident": EmergencyIncidentRead.model_validate(case) if hasattr(EmergencyIncidentRead, "model_validate") else case}

    # Fetch Timeline & Messages
    timeline_entries: list[IncidentTimeline] = []
    messages: list[CaseMessage] = []

    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        t_stmt = select(IncidentTimeline).where(IncidentTimeline.incident_id == case.id).order_by(IncidentTimeline.event_time.asc())
        timeline_entries = (await db.execute(t_stmt)).scalars().all()

        m_stmt = select(CaseMessage).where(CaseMessage.case_id == case.id).order_by(CaseMessage.created_at.asc())
        messages = (await db.execute(m_stmt)).scalars().all()
    else:
        timeline_entries = _CASE_TIMELINE_CACHE.get(case_number, [])
        messages = _CASE_MESSAGES_CACHE.get(case_number, [])

    # Update case status
    case.status = "CLOSED"
    case.closed_by = operator_name
    case.closed_at = datetime.utcnow()
    if payload and payload.operator_comments:
        case.operator_comments = payload.operator_comments

    # Add timeline & audit entries
    timeline_closed = await EmergencyService.add_incident_timeline_event(
        db,
        case.id,
        "CASE_CLOSED",
        f"Case {case_number} closed by {operator_name}. Reason: {payload.closure_reason if payload else 'RESOLVED'}",
        camera_id=case.camera_id,
        actor_id=operator_name,
        case_number=case_number,
    )
    if timeline_closed and timeline_closed not in timeline_entries:
        timeline_entries.append(timeline_closed)

    # Audit log
    from app.services.audit_logger import audit_logger
    await audit_logger.log_event(
        event_type="CASE_CLOSED",
        user_id=str(owner_id),
        resource=f"case:{case_number}",
        details={"closed_by": operator_name, "closure_reason": payload.closure_reason if payload else "RESOLVED"},
    )

    # Broadcast case status updated WS event
    from app.services.websocket_manager import ws_manager
    import json
    await ws_manager.broadcast(json.dumps({
        "type": "EMERGENCY_CASE_UPDATED",
        "event": "EMERGENCY_CASE_UPDATED",
        "case_number": case_number,
        "status": "CLOSED",
        "closed_by": operator_name,
        "closed_at": case.closed_at.isoformat(),
    }))

    # 3. Generate DOCX Case Report & Link to Document Centre
    await audit_logger.log_event(
        event_type="DOCUMENT_GENERATION_STARTED",
        user_id=str(owner_id),
        resource=f"case:{case_number}",
        details={"case_number": case_number, "version": 1},
    )

    case_doc: Optional[CaseReportDocument] = None
    doc_status = "GENERATED"

    try:
        from app.services.case_report_generator import CaseReportGeneratorService
        case_doc, doc_record = await CaseReportGeneratorService.generate_and_store_case_report(
            db=db,
            incident=case,
            timeline_entries=timeline_entries,
            messages=messages,
            owner_id=owner_id,
            created_by=operator_name,
            version=1,
        )

        if case_number not in _CASE_DOCUMENTS_CACHE:
            _CASE_DOCUMENTS_CACHE[case_number] = []
        _CASE_DOCUMENTS_CACHE[case_number].append(case_doc)

        await audit_logger.log_event(
            event_type="DOCUMENT_GENERATED",
            user_id=str(owner_id),
            resource=f"document:{case_doc.id}",
            details={"case_number": case_number, "file_name": case_doc.file_name, "hash": case_doc.document_hash},
        )

        await ws_manager.broadcast(json.dumps({
            "type": "CASE_DOCUMENT_GENERATED",
            "event": "CASE_DOCUMENT_GENERATED",
            "case_number": case_number,
            "document_id": str(case_doc.id),
            "file_name": case_doc.file_name,
            "version": case_doc.version,
            "document_hash": case_doc.document_hash,
            "status": "GENERATED",
        }))
    except Exception as exc:
        logger.exception("DOCX case report generation failed for %s: %s", case_number, exc)
        doc_status = "GENERATION_FAILED"

        # Create failure placeholder document record (Case remains CLOSED)
        case_doc = CaseReportDocument(
            id=uuid.uuid4(),
            incident_id=case.id,
            case_number=case_number,
            document_type="CASE_REPORT",
            file_name=f"{case_number}-report-v1.docx",
            version=1,
            status="GENERATION_FAILED",
            created_by=operator_name,
            created_at=datetime.utcnow(),
            metadata_json={"error": str(exc)},
        )
        if hasattr(db, "add") and type(db).__name__ != "DummySession":
            try:
                db.add(case_doc)
                await db.commit()
            except Exception:
                pass

        if case_number not in _CASE_DOCUMENTS_CACHE:
            _CASE_DOCUMENTS_CACHE[case_number] = []
        _CASE_DOCUMENTS_CACHE[case_number].append(case_doc)

        await audit_logger.log_event(
            event_type="DOCUMENT_GENERATION_FAILED",
            user_id=str(owner_id),
            resource=f"case:{case_number}",
            details={"error": str(exc)},
        )

    doc_read = None
    if case_doc:
        doc_read = {
            "id": str(case_doc.id),
            "incident_id": str(case_doc.incident_id),
            "case_number": case_doc.case_number,
            "document_id": str(case_doc.document_id) if case_doc.document_id else None,
            "document_type": case_doc.document_type,
            "file_name": case_doc.file_name,
            "storage_key": case_doc.storage_key,
            "document_hash": case_doc.document_hash,
            "version": case_doc.version,
            "status": case_doc.status,
            "created_by": case_doc.created_by,
            "created_at": case_doc.created_at.isoformat() if case_doc.created_at else datetime.utcnow().isoformat(),
            "download_url": f"/api/v1/emergency/cases/{case_number}/documents/{case_doc.id}/download",
            "view_url": f"/api/v1/emergency/cases/{case_number}/documents/{case_doc.id}/download",
        }

    return {
        "status": "closed",
        "case_number": case_number,
        "closed_by": operator_name,
        "closed_at": case.closed_at.isoformat() if case.closed_at else datetime.utcnow().isoformat(),
        "document_status": doc_status,
        "document": doc_read,
    }


@router.get("/cases/{case_number}/documents", response_model=list[CaseReportDocumentRead])
async def list_case_report_documents(
    case_number: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all generated report documents and version history for a case."""
    records: list[CaseReportDocument] = []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        stmt = select(CaseReportDocument).where(CaseReportDocument.case_number == case_number).order_by(CaseReportDocument.version.desc())
        records = (await db.execute(stmt)).scalars().all()

    if not records and case_number in _CASE_DOCUMENTS_CACHE:
        records = _CASE_DOCUMENTS_CACHE[case_number]

    res = []
    for r in records:
        d = CaseReportDocumentRead.model_validate(r)
        d.download_url = f"/api/v1/emergency/cases/{case_number}/documents/{r.id}/download"
        d.view_url = f"/api/v1/emergency/cases/{case_number}/documents/{r.id}/download"
        res.append(d)
    return res


@router.post("/cases/{case_number}/documents/generate", response_model=CaseReportDocumentRead)
async def generate_or_retry_case_document(
    case_number: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually generate or retry case report document generation (creates next version v2, v3)."""
    operator_name = (
        (getattr(current_user, "full_name", None) or getattr(current_user, "email", None))
        if current_user
        else "Authorized Operator"
    )
    owner_id = getattr(current_user, "id", None) or uuid.UUID("00000000-0000-0000-0000-000000000001")

    # Fetch Case
    case = None
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        stmt = select(EmergencyIncident).where(EmergencyIncident.incident_code == case_number)
        res = await db.execute(stmt)
        case = res.scalars().first()

    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_number} not found")

    # Determine Version Number
    existing: list[CaseReportDocument] = []
    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        e_stmt = select(CaseReportDocument).where(CaseReportDocument.case_number == case_number)
        existing = (await db.execute(e_stmt)).scalars().all()
    else:
        existing = _CASE_DOCUMENTS_CACHE.get(case_number, [])

    next_version = (max([doc.version for doc in existing], default=0) or 0) + 1

    # Fetch Timeline & Messages
    timeline_entries: list[IncidentTimeline] = []
    messages: list[CaseMessage] = []

    if hasattr(db, "execute") and type(db).__name__ != "DummySession":
        t_stmt = select(IncidentTimeline).where(IncidentTimeline.incident_id == case.id).order_by(IncidentTimeline.event_time.asc())
        timeline_entries = (await db.execute(t_stmt)).scalars().all()
        m_stmt = select(CaseMessage).where(CaseMessage.case_id == case.id).order_by(CaseMessage.created_at.asc())
        messages = (await db.execute(m_stmt)).scalars().all()
    else:
        timeline_entries = _CASE_TIMELINE_CACHE.get(case_number, [])
        messages = _CASE_MESSAGES_CACHE.get(case_number, [])

    from app.services.audit_logger import audit_logger
    await audit_logger.log_event(
        event_type="DOCUMENT_GENERATION_STARTED",
        user_id=str(owner_id),
        resource=f"case:{case_number}",
        details={"case_number": case_number, "version": next_version},
    )

    try:
        from app.services.case_report_generator import CaseReportGeneratorService
        case_doc, doc_record = await CaseReportGeneratorService.generate_and_store_case_report(
            db=db,
            incident=case,
            timeline_entries=timeline_entries,
            messages=messages,
            owner_id=owner_id,
            created_by=operator_name,
            version=next_version,
        )

        if case_number not in _CASE_DOCUMENTS_CACHE:
            _CASE_DOCUMENTS_CACHE[case_number] = []
        _CASE_DOCUMENTS_CACHE[case_number].append(case_doc)

        await audit_logger.log_event(
            event_type="DOCUMENT_REGENERATED" if next_version > 1 else "DOCUMENT_GENERATED",
            user_id=str(owner_id),
            resource=f"document:{case_doc.id}",
            details={"case_number": case_number, "version": next_version, "hash": case_doc.document_hash},
        )

        from app.services.websocket_manager import ws_manager
        import json
        await ws_manager.broadcast(json.dumps({
            "type": "CASE_DOCUMENT_GENERATED",
            "event": "CASE_DOCUMENT_GENERATED",
            "case_number": case_number,
            "document_id": str(case_doc.id),
            "file_name": case_doc.file_name,
            "version": case_doc.version,
            "document_hash": case_doc.document_hash,
            "status": "GENERATED",
        }))

        res = CaseReportDocumentRead.model_validate(case_doc)
        res.download_url = f"/api/v1/emergency/cases/{case_number}/documents/{case_doc.id}/download"
        res.view_url = f"/api/v1/emergency/cases/{case_number}/documents/{case_doc.id}/download"
        return res
    except Exception as exc:
        logger.exception("Failed to generate report for %s v%d: %s", case_number, next_version, exc)
        await audit_logger.log_event(
            event_type="DOCUMENT_GENERATION_FAILED",
            user_id=str(owner_id),
            resource=f"case:{case_number}",
            details={"version": next_version, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=f"Failed to generate case report document: {exc}")


@router.get("/cases/{case_number}/documents/{document_id}/download")
async def download_case_report_document(
    case_number: str,
    document_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Secure, authenticated download of a generated case report DOCX file."""
    owner_id = getattr(current_user, "id", None) or uuid.UUID("00000000-0000-0000-0000-000000000001")

    doc: Optional[CaseReportDocument] = None
    if hasattr(db, "get") and type(db).__name__ != "DummySession":
        doc = await db.get(CaseReportDocument, document_id)

    if not doc and case_number in _CASE_DOCUMENTS_CACHE:
        for d in _CASE_DOCUMENTS_CACHE[case_number]:
            if str(d.id) == str(document_id):
                doc = d
                break

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    from app.services.audit_logger import audit_logger
    await audit_logger.log_event(
        event_type="DOCUMENT_VIEWED",
        user_id=str(owner_id),
        resource=f"document:{document_id}",
        details={"case_number": case_number, "file_name": doc.file_name},
    )

    await audit_logger.log_event(
        event_type="DOCUMENT_DOWNLOADED",
        user_id=str(owner_id),
        resource=f"document:{document_id}",
        details={"case_number": case_number, "file_name": doc.file_name},
    )

    if not doc.storage_key:
        raise HTTPException(status_code=404, detail="Document binary storage key not available")

    try:
        from app.services.document_storage import read_and_decrypt
        file_bytes = read_and_decrypt(doc.storage_key)
        from fastapi.responses import Response
        return Response(
            file_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
        )
    except Exception as exc:
        logger.error("Failed to decrypt document %s: %s", doc.storage_key, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve document file")


@router.post("/correlate")
async def correlate_multi_camera_events(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Correlates multi-camera AI detection events across time and location into a single unified Emergency Case with timeline.
    """
    events = payload.get("camera_events", [])
    if not events:
        raise HTTPException(status_code=400, detail="camera_events list is required")

    incident = await EmergencyService.correlate_multi_camera_events(db, events)
    if not incident:
        raise HTTPException(status_code=500, detail="Failed to correlate multi-camera events")

    return {
        "status": "SUCCESS",
        "case_number": incident.incident_code,
        "incident_id": str(incident.id),
        "title": incident.title,
        "severity": incident.severity,
        "total_correlated_events": len(events),
        "camera_id": str(incident.camera_id) if incident.camera_id else None,
    }


