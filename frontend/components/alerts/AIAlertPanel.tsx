"use client";

import { useState, useEffect } from "react";
import { fetchAPI } from "@/lib/api";

interface AIAlert {
  id: string;
  alert_code: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  status: string;
  camera_id: string;
  confidence: number;
  created_at: string;
}

const severityConfig = {
  CRITICAL: { bg: "bg-red-900", border: "border-red-600", text: "text-red-400" },
  HIGH: { bg: "bg-orange-900", border: "border-orange-600", text: "text-orange-400" },
  MEDIUM: { bg: "bg-yellow-900", border: "border-yellow-600", text: "text-yellow-400" },
  LOW: { bg: "bg-green-900", border: "border-green-600", text: "text-green-400" },
};

export default function AIAlertPanel() {
  const [alerts, setAlerts] = useState<AIAlert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<AIAlert | null>(null);
  const [filter, setFilter] = useState<"all" | "open" | "acknowledged">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 3000);
    return () => clearInterval(interval);
  }, []);

  const loadAlerts = async () => {
    try {
      const data = await fetchAPI<AIAlert[]>("/alerts?limit=50");
      setAlerts(data);
    } catch (error) {
      console.error("Failed to load alerts:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await fetchAPI(`/alerts/${alertId}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ officer_name: "Operator" }),
      });
      loadAlerts();
    } catch (error) {
      console.error("Failed to acknowledge alert:", error);
    }
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === "open") return alert.status === "OPEN";
    if (filter === "acknowledged") return alert.status === "ACKNOWLEDGED";
    return true;
  });

  const criticalCount = alerts.filter((a) => a.severity === "CRITICAL").length;
  const openCount = alerts.filter((a) => a.status === "OPEN").length;

  return (
    <div className="space-y-4">
      {/* Header Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-gradient-to-br from-red-900 to-red-800 p-4 rounded-lg border border-red-700">
          <p className="text-sm text-red-300">Critical</p>
          <p className="text-2xl font-bold text-red-100">{criticalCount}</p>
        </div>
        <div className="bg-gradient-to-br from-orange-900 to-orange-800 p-4 rounded-lg border border-orange-700">
          <p className="text-sm text-orange-300">Open</p>
          <p className="text-2xl font-bold text-orange-100">{openCount}</p>
        </div>
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 p-4 rounded-lg border border-blue-700">
          <p className="text-sm text-blue-300">Total</p>
          <p className="text-2xl font-bold text-blue-100">{alerts.length}</p>
        </div>
        <div className="bg-gradient-to-br from-green-900 to-green-800 p-4 rounded-lg border border-green-700">
          <p className="text-sm text-green-300">Acknowledged</p>
          <p className="text-2xl font-bold text-green-100">
            {alerts.filter((a) => a.status === "ACKNOWLEDGED").length}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(["all", "open", "acknowledged"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded text-sm font-semibold transition ${
              filter === f
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Alerts List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading alerts...</div>
        ) : filteredAlerts.length === 0 ? (
          <div className="text-center py-8 text-gray-400">No alerts found</div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              onClick={() => setSelectedAlert(alert)}
              className={`p-3 rounded border-2 cursor-pointer transition ${
                selectedAlert?.id === alert.id
                  ? `${severityConfig[alert.severity as keyof typeof severityConfig]?.bg} ${severityConfig[alert.severity as keyof typeof severityConfig]?.border}`
                  : "bg-gray-800 border-gray-700 hover:border-gray-600"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded font-semibold ${
                        severityConfig[alert.severity as keyof typeof severityConfig]?.bg
                      } ${severityConfig[alert.severity as keyof typeof severityConfig]?.text}`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-xs text-gray-400">{alert.alert_code}</span>
                  </div>
                  <p className="font-semibold text-sm mt-1">{alert.title}</p>
                  <p className="text-xs text-gray-300 mt-1">{alert.description}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs bg-gray-700 px-2 py-1 rounded">{alert.status}</span>
                    {alert.confidence && (
                      <span className="text-xs text-green-400">
                        {(alert.confidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>
                </div>
                {alert.status === "OPEN" && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAcknowledge(alert.id);
                    }}
                    className="ml-2 bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs font-semibold transition"
                  >
                    Ack
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Selected Alert Details */}
      {selectedAlert && (
        <div className={`p-4 rounded-lg border-2 ${severityConfig[selectedAlert.severity as keyof typeof severityConfig]?.bg} ${severityConfig[selectedAlert.severity as keyof typeof severityConfig]?.border}`}>
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-bold text-lg">{selectedAlert.title}</h3>
              <p className="text-sm text-gray-300 mt-1">{selectedAlert.alert_code}</p>
            </div>
            {selectedAlert.status === "OPEN" && (
              <button
                onClick={() => handleAcknowledge(selectedAlert.id)}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-semibold transition"
              >
                📋 Acknowledge
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-gray-400">Severity</p>
              <p className="font-semibold">{selectedAlert.severity}</p>
            </div>
            <div>
              <p className="text-gray-400">Type</p>
              <p className="font-semibold">{selectedAlert.alert_type}</p>
            </div>
            <div>
              <p className="text-gray-400">Status</p>
              <p className="font-semibold">{selectedAlert.status}</p>
            </div>
            <div>
              <p className="text-gray-400">Confidence</p>
              <p className="font-semibold">{selectedAlert.confidence ? `${(selectedAlert.confidence * 100).toFixed(0)}%` : "N/A"}</p>
            </div>
          </div>
          <div className="mt-3">
            <p className="text-gray-400 text-sm">Description</p>
            <p className="text-sm mt-1">{selectedAlert.description}</p>
          </div>
          <div className="mt-3 text-xs text-gray-400">
            Created: {new Date(selectedAlert.created_at).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}
