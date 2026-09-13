"use client";

import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { fetchAPI } from "@/lib/api";
import MultiCameraMap from "@/components/map/MultiCameraMap";

interface EmergencyIncident {
  id: string;
  incident_code: string;
  case_number?: string;
  sequence_number?: number;
  title?: string;
  incident_type: string;
  severity: string;
  priority?: string;
  camera_id?: string;
  location_latitude?: number;
  location_longitude?: number;
  location_name?: string;
  description: string;
  status: string;
  created_at: string;
  updated_at?: string;
  ai_confidence?: number;
  source_alert_id?: string;
  source_event_id?: string;
  assigned_recipient?: string;
  created_by?: string;
}

interface IncidentTimelineItem {
  id: string;
  case_number?: string;
  event_type: string;
  actor_id?: string;
  event_time: string;
  description: string;
  message?: string;
}

interface Hospital {
  hospital_name: string;
  hospital_phone: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  arrival_minutes: number;
}

interface AmbulanceDispatch {
  id: string;
  ambulance_id: string;
  hospital_name: string;
  status: string;
  estimated_arrival_minutes: number;
}

interface AlertRecipient {
  id: string;
  name: string;
  designation?: string;
  department?: string;
  role?: string;
  phone_number?: string;
  recipient_type: string;
  alert_preference: string;
  is_active: boolean;
}

interface AlertDelivery {
  id: string;
  recipient_id: string;
  recipient_name: string;
  phone_number: string;
  risk_level: string;
  message_text: string;
  status: string;
  is_recurring: boolean;
  send_count: number;
  last_sent_at: string | null;
  next_send_at: string | null;
  stopped_at: string | null;
  provider_message_id: string | null;
  last_error: string | null;
}

const severityColors: Record<string, string> = {
  CRITICAL: "bg-red-900 text-red-100",
  HIGH: "bg-orange-900 text-orange-100",
  MEDIUM: "bg-yellow-900 text-yellow-100",
  LOW: "bg-green-900 text-green-100",
};

function normalizeIndianPhoneNumber(value: string): string | null {
  const compact = value.trim().replace(/[\s().-]/g, "");
  const local = compact.startsWith("+91")
    ? compact.slice(3)
    : compact.startsWith("91") && compact.length === 12
      ? compact.slice(2)
      : compact.startsWith("0") && compact.length === 11
        ? compact.slice(1)
        : compact;
  return /^[6-9]\d{9}$/.test(local) ? `+91${local}` : null;
}

export default function EmergencyResponsePage() {
  const [incidents, setIncidents] = useState<EmergencyIncident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<EmergencyIncident | null>(null);
  const [timeline, setTimeline] = useState<IncidentTimelineItem[]>([]);
  const [hospital, setHospital] = useState<Hospital | null>(null);
  const [ambulance, setAmbulance] = useState<AmbulanceDispatch | null>(null);
  const [customMessage, setCustomMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [alertLevel, setAlertLevel] = useState("NORMAL");
  const [showOTPVerification, setShowOTPVerification] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [otp, setOtp] = useState("");
  const [verificationStep, setVerificationStep] = useState<"phone" | "otp">("phone");
  const [showRecipientModal, setShowRecipientModal] = useState(false);
  const [officerPhone, setOfficerPhone] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [recipientDesignation, setRecipientDesignation] = useState("");
  const [recipientDepartment, setRecipientDepartment] = useState("");
  const [recipientRole, setRecipientRole] = useState("OPERATOR");
  const [recipientIsActive, setRecipientIsActive] = useState(true);
  const [recipients, setRecipients] = useState<AlertRecipient[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<AlertDelivery[]>([]);
  const [selectedRecipientIds, setSelectedRecipientIds] = useState<string[]>([]);
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [riskLevel, setRiskLevel] = useState<"LOW" | "MEDIUM" | "HIGH">("LOW");
  const [dispatchMessage, setDispatchMessage] = useState("");
  const [recipientSubmitting, setRecipientSubmitting] = useState(false);
  const [recipientSaving, setRecipientSaving] = useState(false);
  const [smsTestSubmitting, setSmsTestSubmitting] = useState(false);
  const [smsConfigured, setSmsConfigured] = useState<boolean | null>(null);
  const [recipientNotice, setRecipientNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [caseDocuments, setCaseDocuments] = useState<any[]>([]);

  const loadCaseDocuments = async (caseNum: string) => {
    try {
      const data = await fetchAPI<any[]>(`/emergency/cases/${caseNum}/documents`);
      setCaseDocuments(data);
    } catch {
      setCaseDocuments([]);
    }
  };

  useEffect(() => {
    loadIncidents();
    loadRecipients();
    loadAlertDeliveries();
    fetchAPI<{ configured: boolean }>("/notifications/health").then((health) => setSmsConfigured(health.configured)).catch(() => setSmsConfigured(false));
    
    // Connect to WebSocket for real-time synchronization
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = process.env.NEXT_PUBLIC_WS_HOST || "localhost:8000";
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(`${wsProtocol}//${wsHost}/ws`);
      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          const evtType = data.type || data.event;
          if (["EMERGENCY_CASE_CREATED", "EMERGENCY_CASE_UPDATED", "CASE_CREATED", "CASE_UPDATED", "CASE_STATUS_CHANGED", "MESSAGE_CREATED", "COMMENT_CREATED", "REPLY_CREATED"].includes(evtType)) {
            loadIncidents();
          }
          if (evtType === "RECIPIENT_CREATED") {
            loadRecipients();
          }
          if (evtType === "CASE_DOCUMENT_GENERATED" && data.case_number) {
            loadCaseDocuments(data.case_number);
          }
        } catch (err) {
          console.error("WebSocket message parsing error:", err);
        }
      };
    } catch (e) {
      console.warn("WebSocket connection fallback:", e);
    }

    const interval = setInterval(loadIncidents, 5000);
    const alertInterval = setInterval(loadAlertDeliveries, 10000);
    return () => {
      clearInterval(interval);
      clearInterval(alertInterval);
      if (ws) ws.close();
    };
  }, []);

  const handleTestSms = async () => {
    const normalizedPhone = normalizeIndianPhoneNumber(officerPhone);
    if (!normalizedPhone) {
      setRecipientNotice({ type: "error", text: "Enter a valid Indian mobile number." });
      return;
    }
    setSmsTestSubmitting(true);
    setRecipientNotice(null);
    try {
      await fetchAPI("/notifications/test-sms", {
        method: "POST",
        body: JSON.stringify({ phone_number: normalizedPhone, message: dispatchMessage.trim() || "SENTINEL SMS test." }),
      });
      setRecipientNotice({ type: "success", text: "Test SMS accepted for delivery." });
    } catch (error) {
      setRecipientNotice({ type: "error", text: `SMS test failed: ${error instanceof Error ? error.message : "provider rejected the request."}` });
    } finally {
      setSmsTestSubmitting(false);
    }
  };

  const loadRecipients = async () => {
    try {
      const data = await fetchAPI<AlertRecipient[]>("/emergency/recipients");
      setRecipients(data);
    } catch (error) {
      console.error("Failed to load alert recipients:", error);
    }
  };

  const handleSaveRecipient = async () => {
    const normalizedPhone = officerPhone ? normalizeIndianPhoneNumber(officerPhone) : null;
    if (!recipientName.trim()) {
      setRecipientNotice({ type: "error", text: "Provide a recipient name." });
      return;
    }
    setRecipientSaving(true);
    setRecipientNotice(null);
    try {
      const recipient = await fetchAPI<AlertRecipient>("/emergency/recipients", {
        method: "POST",
        body: JSON.stringify({
          name: recipientName.trim(),
          designation: recipientDesignation.trim() || undefined,
          department: recipientDepartment.trim() || undefined,
          role: recipientRole || "OPERATOR",
          phone_number: normalizedPhone || officerPhone.trim() || undefined,
          alert_preference: "ALL",
          is_active: recipientIsActive,
        }),
      });
      setRecipients((current) => current.some((item) => item.id === recipient.id) ? current : [...current, recipient]);
      setSelectedRecipientIds((current) => [...new Set([...current, recipient.id])]);
      setRecipientName("");
      setRecipientDesignation("");
      setRecipientDepartment("");
      setOfficerPhone("");
      setRecipientNotice({ type: "success", text: "Recipient saved successfully!" });
      await loadRecipients();
    } catch (error) {
      setRecipientNotice({ type: "error", text: error instanceof Error ? error.message : "Recipient could not be saved." });
    } finally {
      setRecipientSaving(false);
    }
  };

  const loadAlertDeliveries = async () => {
    try {
      const data = await fetchAPI<AlertDelivery[]>("/emergency/deliveries");
      setActiveAlerts(data);
    } catch (error) {
      console.error("Failed to load alert status:", error);
    }
  };

  const stopAlert = async (alertId: string) => {
    try {
      await fetchAPI(`/emergency/deliveries/${alertId}/stop`, { method: "POST" });
      setRecipientNotice({ type: "success", text: "Alert stopped. Automatic notifications have been disabled." });
      await loadAlertDeliveries();
    } catch (error) {
      setRecipientNotice({ type: "error", text: error instanceof Error ? error.message : "Alert could not be stopped." });
    }
  };

  const loadIncidents = async () => {
    try {
      let data: EmergencyIncident[] = [];
      try {
        data = await fetchAPI<EmergencyIncident[]>("/emergency/cases");
      } catch {
        data = await fetchAPI<EmergencyIncident[]>("/emergency/incidents?status=OPEN");
      }
      setIncidents(data);
    } catch (error) {
      console.error("Failed to load incidents:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectIncident = async (incident: EmergencyIncident) => {
    setSelectedIncident(incident);
    const caseNum = incident.case_number || incident.incident_code || incident.id;

    loadCaseDocuments(caseNum);

    // Load Timeline
    try {
      const timelineData = await fetchAPI<IncidentTimelineItem[]>(`/emergency/cases/${caseNum}/timeline`);
      setTimeline(timelineData);
    } catch {
      try {
        const timelineData = await fetchAPI<IncidentTimelineItem[]>(`/emergency/incidents/${incident.id}/timeline`);
        setTimeline(timelineData);
      } catch (err) {
        console.error("Failed to load case timeline:", err);
      }
    }

    // Load hospital info
    try {
      const hospitalData = await fetchAPI<{ hospital: Hospital }>(`/emergency/incidents/${incident.id}/find-hospital`);
      setHospital(hospitalData.hospital);
    } catch (error) {
      console.error("Failed to load hospital:", error);
    }
  };

  const handleUpdateCaseStatus = async (newStatus: string) => {
    if (!selectedIncident) return;
    const caseNum = selectedIncident.case_number || selectedIncident.incident_code;
    try {
      if (newStatus === "CLOSED") {
        const res = await fetchAPI<any>(`/emergency/cases/${caseNum}/close`, {
          method: "POST",
          body: JSON.stringify({ closure_reason: "CASE_RESOLVED" }),
        });
        await loadIncidents();
        setSelectedIncident((prev) => prev ? { ...prev, status: "CLOSED", closed_by: res.closed_by, closed_at: res.closed_at } : null);
        await loadCaseDocuments(caseNum);
        const timelineData = await fetchAPI<IncidentTimelineItem[]>(`/emergency/cases/${caseNum}/timeline`);
        setTimeline(timelineData);
      } else {
        const updated = await fetchAPI<EmergencyIncident>(`/emergency/cases/${caseNum}`, {
          method: "PATCH",
          body: JSON.stringify({ status: newStatus }),
        });
        setSelectedIncident(updated);
        await loadIncidents();
        const timelineData = await fetchAPI<IncidentTimelineItem[]>(`/emergency/cases/${caseNum}/timeline`);
        setTimeline(timelineData);
      }
    } catch (err) {
      alert(`Status update note: ${err instanceof Error ? err.message : "Failed to update status"}`);
    }
  };

  const handleRetryDocumentGeneration = async () => {
    if (!selectedIncident) return;
    const caseNum = selectedIncident.case_number || selectedIncident.incident_code;
    try {
      await fetchAPI(`/emergency/cases/${caseNum}/documents/generate`, { method: "POST" });
      await loadCaseDocuments(caseNum);
    } catch (err) {
      alert(`Document generation failed: ${err instanceof Error ? err.message : "Error generating document"}`);
    }
  };

  const handleDispatchAmbulance = async () => {
    if (!selectedIncident || !hospital) return;

    try {
      const result = await fetchAPI<AmbulanceDispatch>(
        `/emergency/incidents/${selectedIncident.id}/ambulance`,
        {
          method: "POST",
          body: JSON.stringify({
            hospital_name: hospital.hospital_name,
            hospital_phone: hospital.hospital_phone,
            hospital_latitude: hospital.latitude,
            hospital_longitude: hospital.longitude,
          }),
        }
      );
      setAmbulance(result);
      alert("Ambulance dispatched successfully!");
    } catch (error) {
      console.error("Failed to dispatch ambulance:", error);
    }
  };

  const handleRequestOTP = async () => {
    try {
      await fetchAPI("/emergency/phone-verification/request-otp", {
        method: "POST",
        body: JSON.stringify({ phone_number: phoneNumber }),
      });
      setVerificationStep("otp");
      alert(`OTP sent to ${phoneNumber}`);
    } catch (error) {
      console.error("Failed to send OTP:", error);
    }
  };

  const handleVerifyOTP = async () => {
    try {
      await fetchAPI("/emergency/phone-verification/verify-otp", {
        method: "POST",
        body: JSON.stringify({ phone_number: phoneNumber, otp }),
      });
      alert("Phone number verified successfully!");
      setShowOTPVerification(false);
      setPhoneNumber("");
      setOtp("");
    } catch (error) {
      console.error("Failed to verify OTP:", error);
    }
  };

  const handleSendAlert = async () => {
    if (!selectedIncident) return;

    try {
      const result = await fetchAPI<{ recipients_count: number }>(
        `/emergency/incidents/${selectedIncident.id}/send-alert`,
        {
          method: "POST",
          body: JSON.stringify({
            alert_level: alertLevel,
            custom_message: customMessage,
          }),
        }
      );
      alert(`Alert sent to ${result.recipients_count} recipients!`);
    } catch (error) {
      console.error("Failed to send alert:", error);
    }
  };

  const handleRecipientSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedPhone = officerPhone ? normalizeIndianPhoneNumber(officerPhone) : null;
    if (officerPhone && !normalizedPhone) {
      setRecipientNotice({ type: "error", text: "Enter a valid Indian mobile number." });
      return;
    }
    if (!dispatchMessage.trim()) {
      setRecipientNotice({ type: "error", text: "Dispatch instructions are required." });
      return;
    }

    setRecipientSubmitting(true);
    setRecipientNotice(null);
    try {
      const nextRecipientIds = selectedRecipientIds;
      if (!nextRecipientIds.length) {
        setRecipientNotice({ type: "error", text: "Select at least one saved recipient or add a new recipient." });
        setRecipientSubmitting(false);
        return;
      }
      const result = await fetchAPI<{
        message: string;
        status: string;
        send_status: string;
        recipient_name: string;
        phone_number: string;
        provider_message_ids: string[];
        next_send_at: string | null;
        reason?: string | null;
      }>("/emergency/recipient-alert", {
        method: "POST",
        body: JSON.stringify({
          recipient_ids: nextRecipientIds,
          risk_level: riskLevel,
          message: dispatchMessage.trim(),
          feedback_message: feedbackMessage.trim() || undefined,
          incident_id: selectedIncident?.id,
          location_latitude: selectedIncident?.location_latitude,
          location_longitude: selectedIncident?.location_longitude,
        }),
      });
      const providerId = result.provider_message_ids?.[0];
      const statusText = result.status === "already_active" ? "already active" : result.send_status;
      setRecipientNotice({
        type: result.status === "sent" ? "success" : "error",
        text: result.status === "failed"
          ? `Alert could not be sent. Reason: ${result.reason || result.message}`
          : `SMS accepted for delivery to ${result.recipient_name} (${result.phone_number}). Status: ${statusText}${providerId ? `. Message ID: ${providerId}` : ""}${result.next_send_at ? `. Next message: ${new Date(result.next_send_at).toLocaleString()}` : ""}`,
      });
      await loadAlertDeliveries();
      setOfficerPhone("");
      setDispatchMessage("");
      setFeedbackMessage("");
    } catch (error) {
      setRecipientNotice({ type: "error", text: error instanceof Error ? error.message : "Unable to dispatch alert." });
    } finally {
      setRecipientSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">🚨 Emergency Response Centre</h1>
          <p className="text-gray-400">AI-Powered Emergency Management & Multi-Camera Monitoring</p>
        </div>

        {selectedIncident && selectedIncident.location_latitude !== null && selectedIncident.location_longitude !== null && (
          <section className="bg-gray-900 rounded-lg border border-gray-800 p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-xl font-bold">Incident Area</h2>
                <p className="text-sm text-gray-400">{selectedIncident.location_name || "Selected incident location"}</p>
              </div>
              {selectedIncident.severity === "HIGH" && (
                <span className="text-xs font-bold uppercase tracking-wide text-red-300">High-risk zone active</span>
              )}
            </div>
            <div className="h-80 overflow-hidden rounded-lg">
              <MultiCameraMap
                cameras={[]}
                incident={selectedIncident as unknown as { location_latitude: number | null; location_longitude: number | null; severity: string }}
              />
            </div>
          </section>
        )}

        {/* OTP Verification Modal */}
        {showOTPVerification && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-900 p-6 rounded-lg max-w-md w-full">
              <h2 className="text-xl font-bold mb-4">Verify Phone Number</h2>
              {verificationStep === "phone" ? (
                <>
                  <input
                    type="tel"
                    placeholder="Enter phone number"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded mb-4 text-white"
                  />
                  <button
                    onClick={handleRequestOTP}
                    className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-semibold"
                  >
                    Send OTP
                  </button>
                </>
              ) : (
                <>
                  <input
                    type="text"
                    placeholder="Enter OTP"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded mb-4 text-white"
                  />
                  <button
                    onClick={handleVerifyOTP}
                    className="w-full bg-green-600 hover:bg-green-700 px-4 py-2 rounded font-semibold mb-2"
                  >
                    Verify OTP
                  </button>
                </>
              )}
              <button
                onClick={() => setShowOTPVerification(false)}
                className="w-full bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {showRecipientModal && (
          <div className="fixed inset-0 z-50 overflow-y-auto bg-black/70 p-3 sm:p-6" role="dialog" aria-modal="true" aria-labelledby="recipient-title">
            <form onSubmit={handleRecipientSubmit} className="mx-auto my-2 max-h-[calc(100vh-1rem)] w-full max-w-lg overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 p-4 shadow-2xl sm:my-4 sm:max-h-[calc(100vh-2rem)] sm:p-6">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <h2 id="recipient-title" className="text-xl font-bold">Add Alert Recipient</h2>
                  <p className="mt-1 text-sm text-gray-400">Dispatch a direct SMS, with a voice escalation for high risk.</p>
                </div>
                <button type="button" onClick={() => setShowRecipientModal(false)} className="text-gray-400 hover:text-white" aria-label="Close">✕</button>
              </div>
              <div className="space-y-4">
                <div className="rounded border border-gray-700 bg-gray-800/60 p-3">
                  <p className="mb-2 text-sm font-semibold">Saved recipients</p>
                  <div className="space-y-2">
                    {recipients.map((recipient) => (
                      <label key={recipient.id} className="flex items-center gap-2 text-sm text-gray-300">
                        <input type="checkbox" checked={selectedRecipientIds.includes(recipient.id)} onChange={(event) => setSelectedRecipientIds((current) => event.target.checked ? [...current, recipient.id] : current.filter((id) => id !== recipient.id))} />
                        <span>{recipient.name} {recipient.phone_number ? `(${recipient.phone_number})` : ""}</span>
                      </label>
                    ))}
                    {!recipients.length && <p className="text-xs text-gray-500">No saved recipients yet. Add one below.</p>}
                  </div>
                </div>
                <label className="block text-sm font-semibold">
                  Recipient Name
                  <input type="text" value={recipientName} onChange={(event) => setRecipientName(event.target.value)} placeholder="Optional: add a new recipient" className="mt-2 w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white outline-none focus:border-blue-500" />
                </label>
                <div className="flex items-center justify-between rounded border border-gray-700 bg-gray-800/60 px-3 py-2 text-xs">
                  <span>SMS SERVICE</span>
                  <span className={smsConfigured ? "text-green-300" : "text-amber-300"}>{smsConfigured ? "● CONFIGURED" : "● DEMO / NOT CONFIGURED"}</span>
                </div>
                <label className="block text-sm font-semibold">
                  Officer Phone Number
                  <input type="tel" value={officerPhone} onChange={(event) => setOfficerPhone(event.target.value)} placeholder="Optional: +919876543210" className="mt-2 w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white outline-none focus:border-blue-500" />
                  {officerPhone && normalizeIndianPhoneNumber(officerPhone) && <span className="mt-1 block text-xs text-green-300">Normalized: {normalizeIndianPhoneNumber(officerPhone)}</span>}
                </label>
                <p className="text-xs text-gray-500">Save a recipient first. Saving a contact never sends an SMS; dispatch is a separate action.</p>
                <label className="block text-sm font-semibold">
                  Risk Level
                  <select value={riskLevel} onChange={(event) => setRiskLevel(event.target.value as typeof riskLevel)} className="mt-2 w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white outline-none focus:border-blue-500">
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                  </select>
                </label>
                <label className="block text-sm font-semibold">
                  Feedback message (optional)
                  <textarea maxLength={2000} rows={2} value={feedbackMessage} onChange={(event) => setFeedbackMessage(event.target.value)} placeholder="Add an operator note for this dispatch..." className="mt-2 w-full resize-none rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white outline-none focus:border-blue-500" />
                </label>
                <label className="block text-sm font-semibold">
                  Message
                  <textarea required minLength={1} maxLength={1000} rows={4} value={dispatchMessage} onChange={(event) => setDispatchMessage(event.target.value)} placeholder="Enter custom dispatch instructions..." className="mt-2 w-full resize-none rounded border border-gray-700 bg-gray-800 px-3 py-2 text-white outline-none focus:border-blue-500" />
                </label>
              </div>
              {recipientNotice && <p className={`mt-4 rounded px-3 py-2 text-sm ${recipientNotice.type === "success" ? "bg-green-900/50 text-green-300" : "bg-red-900/50 text-red-300"}`}>{recipientNotice.text}</p>}
              {activeAlerts.filter((alert) => alert.status === "ACTIVE").map((alert) => (
                <div key={alert.id} className="mt-4 rounded border border-orange-700 bg-orange-950/30 p-3 text-sm">
                  <p className="font-bold text-orange-300">ACTIVE HIGH ALERT</p>
                  <p>{alert.recipient_name} ({alert.phone_number})</p>
                  <p className="text-gray-300">Messages sent: {alert.send_count} | Last sent: {alert.last_sent_at ? new Date(alert.last_sent_at).toLocaleTimeString() : "Not yet"}</p>
                  <p className="text-gray-300">Next message: {alert.next_send_at ? new Date(alert.next_send_at).toLocaleTimeString() : "Pending"}</p>
                  <button type="button" onClick={() => stopAlert(alert.id)} className="mt-2 rounded bg-red-700 px-3 py-1 font-semibold hover:bg-red-600">Stop Alert</button>
                </div>
              ))}
              <div className="mt-6 flex justify-end gap-3">
                <button type="button" onClick={() => setShowRecipientModal(false)} className="rounded bg-gray-700 px-4 py-2 font-semibold hover:bg-gray-600">Cancel</button>
                <button type="button" onClick={handleSaveRecipient} disabled={recipientSaving} className="rounded border border-emerald-500 px-4 py-2 font-semibold text-emerald-200 hover:bg-emerald-900/40 disabled:opacity-60">{recipientSaving ? "Saving..." : "Save Recipient"}</button>
                <button type="button" onClick={handleTestSms} disabled={smsTestSubmitting || smsConfigured === false} className="rounded border border-blue-500 px-4 py-2 font-semibold text-blue-200 hover:bg-blue-900/40 disabled:opacity-60">{smsTestSubmitting ? "Testing..." : "Test SMS"}</button>
                <button type="submit" disabled={recipientSubmitting} className="rounded bg-blue-600 px-4 py-2 font-semibold hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">{recipientSubmitting ? "Sending SMS..." : "Submit Alert"}</button>
              </div>
            </form>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Incidents List */}
          <div className="lg:col-span-1 bg-gray-900 rounded-lg border border-gray-800 p-4">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span className="text-red-500">●</span>
              Active Incidents ({incidents.length})
            </h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {incidents.map((incident) => (
                <div
                  key={incident.id}
                  onClick={() => handleSelectIncident(incident)}
                  className={`p-3 rounded border-2 cursor-pointer transition ${
                    selectedIncident?.id === incident.id
                      ? "border-blue-500 bg-blue-900 bg-opacity-20"
                      : "border-gray-700 hover:border-gray-600"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs px-2 py-1 rounded ${severityColors[incident.severity]}`}>
                      {incident.severity}
                    </span>
                    <span className="text-xs text-gray-400">{incident.incident_code}</span>
                  </div>
                  <p className="font-semibold text-sm">{incident.incident_type}</p>
                  <p className="text-xs text-gray-300">{incident.location_name}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs bg-gray-800 px-2 py-1 rounded">{incident.status}</span>
                    {incident.ai_confidence && (
                      <span className="text-xs text-green-400">
                        Confidence: {(incident.ai_confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Incident Details & Controls */}
          <div className="lg:col-span-2">
            {selectedIncident ? (
              <>
                {/* Incident Summary */}
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
                  <h2 className="text-2xl font-bold mb-4 flex items-center justify-between">
                    <span>{selectedIncident.title || selectedIncident.incident_type}</span>
                    <span className="text-sm bg-blue-900/60 text-blue-200 border border-blue-700 px-3 py-1 rounded font-mono">
                      {selectedIncident.case_number || selectedIncident.incident_code}
                    </span>
                  </h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6 text-sm">
                    <div>
                      <p className="text-gray-400">Case Number</p>
                      <p className="font-semibold font-mono text-blue-300">{selectedIncident.case_number || selectedIncident.incident_code}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Severity</p>
                      <p className={`font-semibold ${severityColors[selectedIncident.severity] || "text-white"}`}>
                        {selectedIncident.severity}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Priority</p>
                      <p className="font-semibold text-yellow-400">{selectedIncident.priority || "HIGH"}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Current Status</p>
                      <p className="font-semibold text-green-400">{selectedIncident.status}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">AI Confidence</p>
                      <p className="font-semibold text-emerald-300">
                        {selectedIncident.ai_confidence ? `${(selectedIncident.ai_confidence * 100).toFixed(0)}%` : "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Detected At</p>
                      <p className="font-semibold">{new Date(selectedIncident.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="mb-4">
                    <p className="text-gray-400 text-sm mb-1">Description</p>
                    <p className="text-gray-300">{selectedIncident.description}</p>
                  </div>

                  {/* Status Workflow Controls */}
                  <div className="mt-4 pt-4 border-t border-gray-800">
                    <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">Advance Case Status Workflow</p>
                    <div className="flex flex-wrap gap-2">
                      {["ACKNOWLEDGED", "IN_PROGRESS", "UNDER_REVIEW", "RESOLVED", "CLOSED"].map((st) => (
                        <button
                          key={st}
                          onClick={() => handleUpdateCaseStatus(st)}
                          disabled={selectedIncident.status === "CLOSED" || selectedIncident.status === st}
                          className={`px-3 py-1.5 rounded text-xs font-bold transition ${
                            selectedIncident.status === st
                              ? "bg-blue-600 text-white cursor-default"
                              : "bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
                          }`}
                        >
                          {st.replace("_", " ")}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Immutable Case Timeline */}
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <span className="text-blue-400">⏱️</span>
                    Immutable Case Timeline
                  </h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {timeline.map((item, idx) => (
                      <div key={item.id || idx} className="flex items-start gap-3 p-2.5 rounded bg-gray-800/50 border border-gray-800 text-xs">
                        <div className="bg-blue-900/60 text-blue-300 px-2 py-1 rounded font-mono font-bold whitespace-nowrap">
                          {item.event_type}
                        </div>
                        <div className="flex-1">
                          <p className="text-gray-200">{item.description || item.message}</p>
                          <p className="text-gray-500 mt-1">
                            By {item.actor_id || "SYSTEM"} • {new Date(item.event_time).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    {!timeline.length && (
                      <p className="text-xs text-gray-500">No timeline entries recorded yet.</p>
                    )}
                  </div>
                </div>

                {/* Generated Case Documents */}
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
                  <h3 className="text-xl font-bold mb-4 flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <span className="text-emerald-400">📄</span>
                      Generated Case Documents
                    </span>
                    {selectedIncident.status === "CLOSED" && (
                      <button
                        onClick={handleRetryDocumentGeneration}
                        className="text-xs bg-blue-700 hover:bg-blue-600 text-white font-bold px-3 py-1.5 rounded transition"
                      >
                        + Generate / Regenerate Report
                      </button>
                    )}
                  </h3>

                  <div className="space-y-3">
                    {caseDocuments.map((doc) => (
                      <div key={doc.id} className="p-3.5 rounded bg-gray-950 border border-gray-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-bold text-blue-300 font-mono text-sm">{doc.file_name}</p>
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800">
                              v{doc.version}
                            </span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${doc.status === "GENERATED" ? "bg-green-950 text-green-300 border-green-800" : "bg-red-950 text-red-300 border-red-800"}`}>
                              {doc.status}
                            </span>
                          </div>
                          {doc.document_hash && (
                            <p className="font-mono text-[11px] text-gray-400 mt-1 truncate" title={doc.document_hash}>
                              SHA-256: {doc.document_hash}
                            </p>
                          )}
                          <p className="text-gray-500 text-[10px] mt-0.5">
                            Created by {doc.created_by || "SYSTEM"} • {new Date(doc.created_at).toLocaleString()}
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          {doc.status === "GENERATED" ? (
                            <>
                              <a
                                href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/emergency/cases/${selectedIncident.case_number || selectedIncident.incident_code}/documents/${doc.id}/download`}
                                target="_blank"
                                rel="noreferrer"
                                className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-1 transition"
                              >
                                👁️ VIEW
                              </a>
                              <a
                                href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/emergency/cases/${selectedIncident.case_number || selectedIncident.incident_code}/documents/${doc.id}/download`}
                                download={doc.file_name}
                                className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1 transition"
                              >
                                📥 DOWNLOAD
                              </a>
                            </>
                          ) : (
                            <button
                              onClick={handleRetryDocumentGeneration}
                              className="px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition"
                            >
                              Retry document generation
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                    {!caseDocuments.length && (
                      <p className="text-xs text-gray-500">No generated report documents available for this case yet. Close case to auto-generate DOCX report.</p>
                    )}
                  </div>
                </div>

                {/* Alert Control */}
                <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <span className="text-yellow-500">🔔</span>
                    Send Alert
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-gray-400 block mb-2">Alert Level</label>
                      <div className="flex gap-2">
                        {["NORMAL", "HIGH", "EMERGENCY"].map((level) => (
                          <button
                            key={level}
                            onClick={() => setAlertLevel(level)}
                            className={`px-4 py-2 rounded font-semibold text-sm transition ${
                              alertLevel === level
                                ? level === "NORMAL"
                                  ? "bg-green-600"
                                  : level === "HIGH"
                                  ? "bg-orange-600"
                                  : "bg-red-600"
                                : "bg-gray-700 hover:bg-gray-600"
                            }`}
                          >
                            {level}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm text-gray-400 block mb-2">Custom Message (for High/Emergency)</label>
                      <textarea
                        value={customMessage}
                        onChange={(e) => setCustomMessage(e.target.value)}
                        placeholder="Enter custom emergency message..."
                        className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded text-white placeholder-gray-500 resize-none"
                        rows={3}
                      />
                    </div>
                    <button
                      onClick={handleSendAlert}
                      className="w-full bg-red-600 hover:bg-red-700 px-6 py-3 rounded font-bold text-lg transition"
                    >
                      📢 SEND ALERT
                    </button>
                  </div>
                </div>

                {/* Hospital & Ambulance Info */}
                {hospital && (
                  <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                      <span className="text-green-500">🏥</span>
                      Nearest Hospital
                    </h3>
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-gray-400 text-sm">Hospital Name</p>
                          <p className="font-semibold">{hospital.hospital_name}</p>
                        </div>
                        <div>
                          <p className="text-gray-400 text-sm">Contact</p>
                          <p className="font-semibold">{hospital.hospital_phone}</p>
                        </div>
                        <div>
                          <p className="text-gray-400 text-sm">Distance</p>
                          <p className="font-semibold">{hospital.distance_km} km</p>
                        </div>
                        <div>
                          <p className="text-gray-400 text-sm">Est. Arrival</p>
                          <p className="font-semibold">{hospital.arrival_minutes} mins</p>
                        </div>
                      </div>
                      <button
                        onClick={handleDispatchAmbulance}
                        className="w-full bg-green-600 hover:bg-green-700 px-4 py-2 rounded font-semibold transition"
                      >
                        🚑 DISPATCH AMBULANCE
                      </button>
                    </div>
                  </div>
                )}

                {ambulance && (
                  <div className="bg-green-900 bg-opacity-20 border border-green-700 rounded-lg p-4">
                    <p className="text-green-400 font-semibold">✓ Ambulance Dispatched</p>
                    <p className="text-sm text-green-300 mt-1">
                      ID: {ambulance.ambulance_id} - Status: {ambulance.status}
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-gray-900 rounded-lg border border-gray-800 p-12 text-center">
                <p className="text-gray-400">Select an incident to view details</p>
              </div>
            )}
          </div>
        </div>

        {/* Recipient Management */}
        <div className="mt-6 bg-gray-900 rounded-lg border border-gray-800 p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="text-blue-500">👥</span>
            Alert Recipients
          </h3>
          <button
            onClick={() => {
              setRecipientNotice(null);
              setShowRecipientModal(true);
            }}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-semibold transition"
          >
            + Add New Recipient
          </button>
            <div className="mt-4 space-y-2">
              {recipients.map((recipient) => <div key={recipient.id} className="flex items-center justify-between rounded border border-gray-800 px-3 py-2 text-sm"><span>{recipient.name}</span><span className="text-gray-400">{recipient.phone_number || "Verified phone"}</span></div>)}
            </div>
        </div>
      </div>
    </div>
  );
}
