"use client";

import { useState, useEffect } from "react";
import { fetchAPI } from "@/lib/api";

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
  location_name?: string;
  description: string;
  status: string;
  created_at: string;
  updated_at?: string;
  ai_confidence?: number;
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

interface CaseMessage {
  id: string;
  case_id: string;
  case_number: string;
  sender_id: string;
  sender_name?: string;
  recipient_id?: string;
  message: string;
  message_type: "RESPONSE" | "COMMENT" | "REPLY" | "SYSTEM_EVENT";
  parent_message_id?: string;
  read_at?: string;
  status: string;
  created_at: string;
  updated_at?: string;
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

const severityColors: Record<string, string> = {
  CRITICAL: "bg-red-900 text-red-100 border-red-700",
  HIGH: "bg-orange-900 text-orange-100 border-orange-700",
  MEDIUM: "bg-yellow-900 text-yellow-100 border-yellow-700",
  LOW: "bg-green-900 text-green-100 border-green-700",
};

const statusColors: Record<string, string> = {
  OPEN: "bg-red-950 text-red-300 border-red-800",
  ACKNOWLEDGED: "bg-yellow-950 text-yellow-300 border-yellow-800",
  IN_PROGRESS: "bg-blue-950 text-blue-300 border-blue-800",
  UNDER_REVIEW: "bg-purple-950 text-purple-300 border-purple-800",
  RESOLVED: "bg-emerald-950 text-emerald-300 border-emerald-800",
  CLOSED: "bg-gray-800 text-gray-400 border-gray-700",
};

export default function ResponseCentrePage() {
  const [incidents, setIncidents] = useState<EmergencyIncident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<EmergencyIncident | null>(null);
  const [timeline, setTimeline] = useState<IncidentTimelineItem[]>([]);
  const [messages, setMessages] = useState<CaseMessage[]>([]);
  const [recipients, setRecipients] = useState<AlertRecipient[]>([]);
  
  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  
  // Active Tab
  const [activeTab, setActiveTab] = useState<"timeline" | "messages" | "comments">("messages");

  // Response Box State
  const [responseMessage, setResponseMessage] = useState("");
  const [selectedRecipientId, setSelectedRecipientId] = useState<string>("");
  const [sendingResponse, setSendingResponse] = useState(false);

  // Comment State
  const [commentText, setCommentText] = useState("");
  const [addingComment, setAddingComment] = useState(false);

  // Reply State
  const [replyingToMessage, setReplyingToMessage] = useState<CaseMessage | null>(null);
  const [replyText, setReplyText] = useState("");
  const [sendingReply, setSendingReply] = useState(false);

  // Add Recipient Modal
  const [showRecipientModal, setShowRecipientModal] = useState(false);
  const [recipName, setRecipName] = useState("");
  const [recipDesignation, setRecipDesignation] = useState("");
  const [recipDepartment, setRecipDepartment] = useState("");
  const [recipRole, setRecipRole] = useState("OPERATOR");
  const [recipPhone, setRecipPhone] = useState("");
  const [recipActive, setRecipActive] = useState(true);
  const [recipNotice, setRecipNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [savingRecipient, setSavingRecipient] = useState(false);

  // Unread Count System & WebSocket
  const [unreadMap, setUnreadMap] = useState<Record<string, number>>({});
  const [wsConnected, setWsConnected] = useState(false);
  const [notificationBellCount, setNotificationBellCount] = useState(0);

  useEffect(() => {
    loadIncidents();
    loadRecipients();

    // Setup WebSocket
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = process.env.NEXT_PUBLIC_WS_HOST || "localhost:8000";
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(`${wsProtocol}//${wsHost}/ws`);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          const evtType = data.type || data.event;

          if (["EMERGENCY_CASE_CREATED", "EMERGENCY_CASE_UPDATED", "CASE_CREATED", "CASE_UPDATED", "CASE_STATUS_CHANGED"].includes(evtType)) {
            loadIncidents();
            if (selectedIncident) {
              loadTimeline(selectedIncident.case_number || selectedIncident.incident_code);
            }
          }

          if (["MESSAGE_CREATED", "COMMENT_CREATED", "REPLY_CREATED"].includes(evtType)) {
            const caseNum = data.case_number;
            if (selectedIncident && (selectedIncident.case_number === caseNum || selectedIncident.incident_code === caseNum)) {
              loadCaseMessages(caseNum);
              loadTimeline(caseNum);
            } else if (caseNum) {
              setUnreadMap((prev) => ({ ...prev, [caseNum]: (prev[caseNum] || 0) + 1 }));
              setNotificationBellCount((prev) => prev + 1);
            }
          }

          if (evtType === "MESSAGE_READ" && data.case_number) {
            setUnreadMap((prev) => ({ ...prev, [data.case_number]: 0 }));
          }

          if (evtType === "RECIPIENT_CREATED") {
            loadRecipients();
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
      };
    } catch (e) {
      console.warn("WebSocket init error:", e);
    }

    const interval = setInterval(loadIncidents, 6000);
    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, []);

  const loadIncidents = async () => {
    try {
      const data = await fetchAPI<EmergencyIncident[]>("/emergency/cases");
      setIncidents(data);
      if (data.length > 0 && !selectedIncident) {
        handleSelectCase(data[0]);
      }
    } catch (err) {
      console.error("Failed to load emergency cases:", err);
    }
  };

  const loadRecipients = async () => {
    try {
      const data = await fetchAPI<AlertRecipient[]>("/emergency/recipients");
      setRecipients(data);
    } catch (err) {
      console.error("Failed to load recipients:", err);
    }
  };

  const handleSelectCase = async (inc: EmergencyIncident) => {
    const caseNum = inc.case_number || inc.incident_code;
    setSelectedIncident(inc);
    await loadCaseMessages(caseNum);
    await loadTimeline(caseNum);

    // Mark messages as read on server
    try {
      await fetchAPI(`/emergency/cases/${caseNum}/read`, { method: "POST" });
      setUnreadMap((prev) => ({ ...prev, [caseNum]: 0 }));
    } catch (err) {
      console.error("Failed to mark messages as read:", err);
    }
  };

  const loadCaseMessages = async (caseNum: string) => {
    try {
      const msgs = await fetchAPI<CaseMessage[]>(`/emergency/cases/${caseNum}/messages`);
      setMessages(msgs);
    } catch (err) {
      console.error("Failed to load case messages:", err);
    }
  };

  const loadTimeline = async (caseNum: string) => {
    try {
      const items = await fetchAPI<IncidentTimelineItem[]>(`/emergency/cases/${caseNum}/timeline`);
      setTimeline(items);
    } catch (err) {
      console.error("Failed to load case timeline:", err);
    }
  };

  const handleSendResponse = async () => {
    if (!selectedIncident || !responseMessage.trim()) return;
    const caseNum = selectedIncident.case_number || selectedIncident.incident_code;
    setSendingResponse(true);
    try {
      await fetchAPI(`/emergency/cases/${caseNum}/messages`, {
        method: "POST",
        body: JSON.stringify({
          message: responseMessage.trim(),
          message_type: "RESPONSE",
          recipient_id: selectedRecipientId || undefined,
          sender_id: "Command Officer",
        }),
      });
      setResponseMessage("");
      await loadCaseMessages(caseNum);
      await loadTimeline(caseNum);
    } catch (err) {
      alert(`Failed to send response: ${err instanceof Error ? err.message : "Network error"}`);
    } finally {
      setSendingResponse(false);
    }
  };

  const handleAddComment = async () => {
    if (!selectedIncident || !commentText.trim()) return;
    const caseNum = selectedIncident.case_number || selectedIncident.incident_code;
    setAddingComment(true);
    try {
      await fetchAPI(`/emergency/cases/${caseNum}/comments`, {
        method: "POST",
        body: JSON.stringify({
          comment: commentText.trim(),
          sender_id: "Camera Operator",
        }),
      });
      setCommentText("");
      await loadCaseMessages(caseNum);
      await loadTimeline(caseNum);
    } catch (err) {
      alert(`Failed to add comment: ${err instanceof Error ? err.message : "Network error"}`);
    } finally {
      setAddingComment(false);
    }
  };

  const handleSendReply = async () => {
    if (!replyingToMessage || !replyText.trim() || !selectedIncident) return;
    const caseNum = selectedIncident.case_number || selectedIncident.incident_code;
    setSendingReply(true);
    try {
      await fetchAPI(`/emergency/messages/${replyingToMessage.id}/reply`, {
        method: "POST",
        body: JSON.stringify({
          message: replyText.trim(),
          sender_id: "Command Officer",
        }),
      });
      setReplyText("");
      setReplyingToMessage(null);
      await loadCaseMessages(caseNum);
      await loadTimeline(caseNum);
    } catch (err) {
      alert(`Failed to send reply: ${err instanceof Error ? err.message : "Network error"}`);
    } finally {
      setSendingReply(false);
    }
  };

  const handleSaveRecipient = async () => {
    if (!recipName.trim()) {
      setRecipNotice({ type: "error", text: "Recipient name is required." });
      return;
    }
    setSavingRecipient(true);
    setRecipNotice(null);
    try {
      await fetchAPI("/emergency/recipients", {
        method: "POST",
        body: JSON.stringify({
          name: recipName.trim(),
          designation: recipDesignation.trim() || undefined,
          department: recipDepartment.trim() || undefined,
          role: recipRole || "OPERATOR",
          phone_number: recipPhone.trim() || undefined,
          is_active: recipActive,
        }),
      });
      setRecipName("");
      setRecipDesignation("");
      setRecipDepartment("");
      setRecipPhone("");
      setRecipNotice({ type: "success", text: "Recipient saved successfully!" });
      await loadRecipients();
      setTimeout(() => setShowRecipientModal(false), 1200);
    } catch (err) {
      setRecipNotice({ type: "error", text: err instanceof Error ? err.message : "Failed to save recipient" });
    } finally {
      setSavingRecipient(false);
    }
  };

  // Filtered Incidents
  const filteredIncidents = incidents.filter((inc) => {
    const caseNum = (inc.case_number || inc.incident_code).toLowerCase();
    const title = (inc.title || inc.incident_type || "").toLowerCase();
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch = !q || caseNum.includes(q) || title.includes(q);
    const matchesStatus = statusFilter === "ALL" || inc.status === statusFilter;
    const matchesPriority = priorityFilter === "ALL" || (inc.priority || "HIGH") === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  // Organize Threaded Messages
  const topLevelMessages = messages.filter((m) => !m.parent_message_id);
  const getReplies = (parentId: string) => messages.filter((m) => m.parent_message_id === parentId);

  return (
    <div className="min-h-screen bg-black text-white p-6 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-4 border-b border-gray-800">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-2xl">🚨</span>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              SENTINEL Emergency Response Centre
            </h1>
            <span className="bg-blue-900/50 text-blue-300 border border-blue-700 text-xs px-2.5 py-0.5 rounded font-mono">
              Real-Time Case Communication
            </span>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            Central Command & Dispatch for AI CCTV Alerts and Police Intelligence Operations
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* WebSocket Status Indicator */}
          <div className="flex items-center gap-2 text-xs bg-gray-900 border border-gray-800 px-3 py-1.5 rounded">
            <span className={`h-2.5 w-2.5 rounded-full ${wsConnected ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`} />
            <span className="text-gray-300 font-mono">
              {wsConnected ? "LIVE SYNC ACTIVE" : "DISCONNECTED"}
            </span>
          </div>

          {/* Notification Bell */}
          <button 
            onClick={() => setNotificationBellCount(0)}
            className="relative p-2 bg-gray-900 border border-gray-800 hover:bg-gray-800 rounded transition"
            title="Notifications"
          >
            <span className="text-xl">🔔</span>
            {notificationBellCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
                {notificationBellCount}
              </span>
            )}
          </button>

          {/* Add Recipient Trigger */}
          <button
            onClick={() => {
              setRecipNotice(null);
              setShowRecipientModal(true);
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded transition flex items-center gap-2"
          >
            <span>+</span> Add Recipient
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT COLUMN: Case List & Filters */}
        <div className="lg:col-span-1 bg-gray-900 rounded-lg border border-gray-800 p-4 flex flex-col h-[calc(100vh-140px)]">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-red-500">●</span> Case Directory ({filteredIncidents.length})
            </h2>
          </div>

          {/* Search Box */}
          <div className="mb-3">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search case e.g. CASE-10000000..."
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500 font-mono"
            />
          </div>

          {/* Filters */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-xs text-white outline-none focus:border-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="UNDER_REVIEW">UNDER_REVIEW</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CLOSED">CLOSED</option>
            </select>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-xs text-white outline-none focus:border-blue-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          {/* Case List Scrollable Area */}
          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {filteredIncidents.map((inc) => {
              const caseNum = inc.case_number || inc.incident_code;
              const isSelected = selectedIncident?.id === inc.id;
              const unread = unreadMap[caseNum] || 0;

              return (
                <div
                  key={inc.id}
                  onClick={() => handleSelectCase(inc)}
                  className={`p-3.5 rounded border transition cursor-pointer relative ${
                    isSelected
                      ? "bg-blue-950/40 border-blue-500 shadow-md"
                      : "bg-gray-950 border-gray-800 hover:border-gray-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-sm font-bold text-blue-300">
                      {caseNum}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold border ${severityColors[inc.severity] || "bg-gray-800 text-gray-300"}`}>
                        {inc.severity}
                      </span>
                      {unread > 0 && (
                        <span className="bg-red-600 text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                          +{unread} new
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="font-semibold text-sm text-gray-200 truncate">
                    {inc.title || inc.incident_type}
                  </p>
                  
                  <p className="text-xs text-gray-400 truncate mt-0.5">
                    {inc.location_name || "Ring Road Junction North"}
                  </p>

                  <div className="mt-2.5 flex items-center justify-between text-xs">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${statusColors[inc.status] || "bg-gray-800 text-gray-300"}`}>
                      {inc.status}
                    </span>
                    <span className="text-gray-500 font-mono text-[10px]">
                      {new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              );
            })}

            {filteredIncidents.length === 0 && (
              <div className="p-8 text-center text-gray-500 text-sm">
                No matching emergency cases found.
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Case Details & Communication Hub */}
        <div className="lg:col-span-2 flex flex-col h-[calc(100vh-140px)]">
          {selectedIncident ? (
            <div className="bg-gray-900 rounded-lg border border-gray-800 flex flex-col h-full overflow-hidden">
              {/* Header Info Banner */}
              <div className="p-4 bg-gray-950 border-b border-gray-800">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-bold text-white">
                        {selectedIncident.title || selectedIncident.incident_type}
                      </h2>
                      <span className="text-sm font-mono text-blue-300 bg-blue-950 px-2.5 py-1 rounded border border-blue-800">
                        {selectedIncident.case_number || selectedIncident.incident_code}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {selectedIncident.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2.5 py-1 rounded font-bold border ${severityColors[selectedIncident.severity]}`}>
                      {selectedIncident.severity}
                    </span>
                    <span className={`text-xs px-2.5 py-1 rounded font-bold border ${statusColors[selectedIncident.status]}`}>
                      {selectedIncident.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Communication Tabs */}
              <div className="flex border-b border-gray-800 bg-gray-900/80 px-4">
                <button
                  onClick={() => setActiveTab("messages")}
                  className={`py-3 px-4 font-semibold text-sm border-b-2 transition ${
                    activeTab === "messages"
                      ? "border-blue-500 text-blue-400"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  }`}
                >
                  💬 Messages & Responses ({messages.length})
                </button>
                <button
                  onClick={() => setActiveTab("timeline")}
                  className={`py-3 px-4 font-semibold text-sm border-b-2 transition ${
                    activeTab === "timeline"
                      ? "border-blue-500 text-blue-400"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  }`}
                >
                  📜 Immutable Timeline ({timeline.length})
                </button>
                <button
                  onClick={() => setActiveTab("comments")}
                  className={`py-3 px-4 font-semibold text-sm border-b-2 transition ${
                    activeTab === "comments"
                      ? "border-blue-500 text-blue-400"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  }`}
                >
                  📝 Operator Comments ({messages.filter((m) => m.message_type === "COMMENT").length})
                </button>
              </div>

              {/* Tab Body */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* MESSAGES & RESPONSES TAB */}
                {activeTab === "messages" && (
                  <div className="space-y-4">
                    {topLevelMessages.map((msg) => {
                      const replies = getReplies(msg.id);

                      return (
                        <div key={msg.id} className="bg-gray-950 border border-gray-800 rounded-lg p-4 space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-sm text-blue-300">
                                {msg.sender_name || msg.sender_id}
                              </span>
                              <span className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono">
                                {msg.message_type}
                              </span>
                            </div>
                            <span className="text-xs text-gray-500 font-mono">
                              {new Date(msg.created_at).toLocaleString()}
                            </span>
                          </div>

                          <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
                            {msg.message}
                          </p>

                          <div className="flex items-center justify-between pt-2 border-t border-gray-800 text-xs">
                            <span className="text-gray-500">
                              Status: <strong className="text-gray-300">{msg.status}</strong> {msg.read_at && `• Read ${new Date(msg.read_at).toLocaleTimeString()}`}
                            </span>
                            <button
                              onClick={() => {
                                setReplyingToMessage(msg);
                                setReplyText("");
                              }}
                              className="text-blue-400 hover:text-blue-300 font-semibold"
                            >
                              ↩ Reply to Thread
                            </button>
                          </div>

                          {/* Render Threaded Replies */}
                          {replies.length > 0 && (
                            <div className="ml-6 mt-3 space-y-2 border-l-2 border-blue-900 pl-3">
                              {replies.map((reply) => (
                                <div key={reply.id} className="bg-gray-900 border border-gray-800 rounded p-2.5 text-xs space-y-1">
                                  <div className="flex items-center justify-between text-gray-400">
                                    <span className="font-bold text-blue-300">{reply.sender_name || reply.sender_id}</span>
                                    <span className="font-mono text-[10px]">{new Date(reply.created_at).toLocaleTimeString()}</span>
                                  </div>
                                  <p className="text-gray-200">{reply.message}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}

                    {messages.length === 0 && (
                      <div className="p-8 text-center text-gray-500 text-sm">
                        No responses or messages posted for this case yet. Use the Response Box below to dispatch.
                      </div>
                    )}
                  </div>
                )}

                {/* TIMELINE TAB */}
                {activeTab === "timeline" && (
                  <div className="space-y-3">
                    {timeline.map((item, idx) => (
                      <div key={item.id || idx} className="flex gap-3 text-xs bg-gray-950 border border-gray-800 rounded p-3">
                        <div className="text-gray-500 font-mono w-24 shrink-0">
                          {new Date(item.event_time).toLocaleTimeString()}
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-blue-400 font-mono">{item.event_type}</span>
                            <span className="text-gray-500">Actor: {item.actor_id || "SYSTEM"}</span>
                          </div>
                          <p className="text-gray-300">{item.description || item.message}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* OPERATOR COMMENTS TAB */}
                {activeTab === "comments" && (
                  <div className="space-y-4">
                    <div className="bg-gray-950 border border-gray-800 rounded-lg p-4">
                      <h4 className="text-sm font-bold text-white mb-2">Add Operator Comment</h4>
                      <textarea
                        rows={2}
                        value={commentText}
                        onChange={(e) => setCommentText(e.target.value)}
                        placeholder="e.g. Camera operator reports movement toward Gate 3..."
                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500 resize-none"
                      />
                      <div className="mt-2 flex justify-end">
                        <button
                          onClick={handleAddComment}
                          disabled={addingComment || !commentText.trim()}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-4 py-2 rounded transition disabled:opacity-50"
                        >
                          {addingComment ? "Saving..." : "Add Comment"}
                        </button>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {messages.filter((m) => m.message_type === "COMMENT").map((cmt) => (
                        <div key={cmt.id} className="bg-gray-950 border border-gray-800 rounded p-3 text-xs space-y-1">
                          <div className="flex items-center justify-between text-gray-400">
                            <span className="font-bold text-yellow-400">{cmt.sender_id}</span>
                            <span className="font-mono">{new Date(cmt.created_at).toLocaleString()}</span>
                          </div>
                          <p className="text-gray-200 text-sm">{cmt.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* REPLY MODAL OVERLAY */}
              {replyingToMessage && (
                <div className="p-3 bg-blue-950/40 border-t border-blue-800 flex items-center justify-between gap-3 text-xs">
                  <div className="truncate flex-1">
                    <span className="font-bold text-blue-300">Replying to {replyingToMessage.sender_id}: </span>
                    <span className="text-gray-300 italic truncate">&quot;{replyingToMessage.message}&quot;</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      placeholder="Write reply..."
                      className="bg-gray-900 border border-gray-700 rounded px-2.5 py-1 text-white outline-none focus:border-blue-500 w-64"
                    />
                    <button
                      onClick={handleSendReply}
                      disabled={sendingReply || !replyText.trim()}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded font-semibold transition disabled:opacity-50"
                    >
                      {sendingReply ? "Sending..." : "Reply"}
                    </button>
                    <button
                      onClick={() => setReplyingToMessage(null)}
                      className="text-gray-400 hover:text-white px-1"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}

              {/* BOTTOM: RESPONSE BOX */}
              <div className="p-4 bg-gray-950 border-t border-gray-800 space-y-3">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span className="font-bold text-white uppercase tracking-wider">
                    CASE RESPONSE — <span className="font-mono text-blue-400">{selectedIncident.case_number || selectedIncident.incident_code}</span>
                  </span>
                  <span>Recipient / Unit Assignment:</span>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                  <select
                    value={selectedRecipientId}
                    onChange={(e) => setSelectedRecipientId(e.target.value)}
                    className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs text-white outline-none focus:border-blue-500 sm:w-64"
                  >
                    <option value="">-- All Units / Broadcast --</option>
                    {recipients.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name} ({r.role || r.recipient_type}) {r.phone_number ? `- ${r.phone_number}` : ""}
                      </option>
                    ))}
                  </select>

                  <div className="flex-1 flex gap-2">
                    <textarea
                      rows={2}
                      value={responseMessage}
                      onChange={(e) => setResponseMessage(e.target.value)}
                      placeholder="Write formal response or tactical dispatch instructions for this case..."
                      className="flex-1 bg-gray-900 border border-gray-700 rounded p-2 text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500 resize-none font-sans"
                    />
                    <button
                      onClick={handleSendResponse}
                      disabled={sendingResponse || !responseMessage.trim()}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm px-6 py-2 rounded transition disabled:opacity-50 shrink-0"
                    >
                      {sendingResponse ? "SENDING..." : "SEND RESPONSE"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-12 text-center h-full flex flex-col items-center justify-center">
              <p className="text-gray-400 text-base">Select an Emergency Case from the left panel to view communication thread.</p>
            </div>
          )}
        </div>
      </div>

      {/* RECIPIENT MODAL */}
      {showRecipientModal && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>👥</span> Add New Alert Recipient
              </h3>
              <button
                onClick={() => setShowRecipientModal(false)}
                className="text-gray-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-gray-400 text-xs font-semibold mb-1">Full Name *</label>
                <input
                  type="text"
                  value={recipName}
                  onChange={(e) => setRecipName(e.target.value)}
                  placeholder="Officer / Inspector Name"
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-400 text-xs font-semibold mb-1">Designation</label>
                  <input
                    type="text"
                    value={recipDesignation}
                    onChange={(e) => setRecipDesignation(e.target.value)}
                    placeholder="e.g. Sub-Inspector"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 text-xs font-semibold mb-1">Department</label>
                  <input
                    type="text"
                    value={recipDepartment}
                    onChange={(e) => setRecipDepartment(e.target.value)}
                    placeholder="e.g. Control Room"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-400 text-xs font-semibold mb-1">Role / Unit</label>
                  <select
                    value={recipRole}
                    onChange={(e) => setRecipRole(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white outline-none focus:border-blue-500"
                  >
                    <option value="OPERATOR">OPERATOR</option>
                    <option value="POLICE">POLICE</option>
                    <option value="EMERGENCY">EMERGENCY</option>
                    <option value="HOSPITAL">HOSPITAL</option>
                    <option value="SUPERVISOR">SUPERVISOR</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 text-xs font-semibold mb-1">Contact Number</label>
                  <input
                    type="tel"
                    value={recipPhone}
                    onChange={(e) => setRecipPhone(e.target.value)}
                    placeholder="+919876543210"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="recipActiveCheck"
                  checked={recipActive}
                  onChange={(e) => setRecipActive(e.target.checked)}
                  className="rounded bg-gray-800 border-gray-700 text-blue-600 focus:ring-0"
                />
                <label htmlFor="recipActiveCheck" className="text-xs text-gray-300 cursor-pointer">
                  Active Recipient (Eligible for Case Dispatch)
                </label>
              </div>

              {recipNotice && (
                <p className={`p-2.5 rounded text-xs ${recipNotice.type === "success" ? "bg-emerald-900/60 text-emerald-300" : "bg-red-900/60 text-red-300"}`}>
                  {recipNotice.text}
                </p>
              )}
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-800">
              <button
                type="button"
                onClick={() => setShowRecipientModal(false)}
                className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveRecipient}
                disabled={savingRecipient}
                className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded text-xs font-bold transition disabled:opacity-50"
              >
                {savingRecipient ? "Saving..." : "Save Recipient"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
