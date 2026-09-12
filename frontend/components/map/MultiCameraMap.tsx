"use client";

import { useEffect, useRef, useState } from "react";
import { Loader } from "@googlemaps/js-api-loader";
import type { Camera } from "@/lib/types";

interface MultiCameraMapProps {
  cameras: Camera[];
  alerts?: Array<{ camera_id?: string; severity?: string; title?: string }>;
  selectedCamera?: Camera | null;
  onSelectCamera?: (camera: Camera) => void;
  incident?: {
    location_latitude: number | null;
    location_longitude: number | null;
    severity: string;
  } | null;
}

export default function MultiCameraMap({ cameras, alerts = [], selectedCamera, onSelectCamera, incident }: MultiCameraMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<Map<string, google.maps.Marker>>(new Map());
  const infoWindowsRef = useRef<Map<string, google.maps.InfoWindow>>(new Map());
  const listenersRef = useRef<google.maps.MapsEventListener[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const initMap = async () => {
      try {
        const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
        if (!apiKey || apiKey === "your_google_maps_api_key_here") {
          setMapError("Google Maps API key is not configured.");
          return;
        }
        const loader = new Loader({
          apiKey,
          version: "weekly",
        });

        const mapsLib = (await loader.importLibrary("maps")) as any;
        const { Map, Marker, InfoWindow } = mapsLib;

        if (cancelled || !mapRef.current || googleMapRef.current) return;

        // Gujarat-wide command-centre view.
        const defaultCenter = {
          lat: 22.45,
          lng: 71.75,
        };

        // Create map
        googleMapRef.current = new Map(mapRef.current, {
          zoom: 7,
          center: defaultCenter,
          mapTypeId: "roadmap",
          mapTypeControl: true,
          fullscreenControl: true,
          zoomControl: true,
          streetViewControl: false,
          gestureHandling: "greedy",
          styles: [
            {
              elementType: "geometry",
              stylers: [{ color: "#1a1a2e" }],
            },
            {
              elementType: "labels.text.stroke",
              stylers: [{ color: "#1a1a2e" }],
            },
            {
              elementType: "labels.text.fill",
              stylers: [{ color: "#ffffff" }],
            },
            {
              featureType: "administrative.locality",
              elementType: "labels.text.fill",
              stylers: [{ color: "#ffffff" }],
            },
            {
              featureType: "poi",
              elementType: "labels.text.fill",
              stylers: [{ color: "#ffffff" }],
            },
            {
              featureType: "poi.park",
              elementType: "geometry.fill",
              stylers: [{ color: "#1a5f1a" }],
            },
            {
              featureType: "road",
              elementType: "geometry.fill",
              stylers: [{ color: "#2c3e50" }],
            },
            {
              featureType: "road",
              elementType: "geometry.stroke",
              stylers: [{ color: "#212a3f" }],
            },
            {
              featureType: "road.arterial",
              elementType: "geometry.fill",
              stylers: [{ color: "#3d5a6c" }],
            },
            {
              featureType: "water",
              elementType: "geometry.fill",
              stylers: [{ color: "#0d3d56" }],
            },
          ],
        });

      } catch (error) {
        console.error("Failed to initialize Google Map:", error);
        setMapError("Map failed to load. Check the Google Maps API key and enabled APIs.");
      }
    };

    initMap();

    return () => {
      cancelled = true;
      listenersRef.current.forEach((listener) => listener.remove());
      listenersRef.current = [];
      markersRef.current.forEach((marker) => marker.setMap(null));
      markersRef.current.clear();
      infoWindowsRef.current.clear();
      googleMapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!googleMapRef.current || typeof google === "undefined") return;
    const { Marker, InfoWindow } = google.maps;
    const validIds = new Set(cameras.map((camera) => camera.id));
    markersRef.current.forEach((marker, cameraId) => {
      if (!validIds.has(cameraId)) {
        marker.setMap(null);
        markersRef.current.delete(cameraId);
        infoWindowsRef.current.delete(cameraId);
      }
    });

    cameras.forEach((camera) => {
      if (typeof camera.latitude !== "number" || typeof camera.longitude !== "number") return;
      const hasAlert = alerts.some((alert) => alert.camera_id === camera.id);
      const markerColor = hasAlert ? "#e11d48" : camera.status === "ONLINE" ? "#10b981" : camera.status === "OFFLINE" ? "#ef4444" : "#f59e0b";
      const icon = { path: google.maps.SymbolPath.CIRCLE, fillColor: markerColor, fillOpacity: 1, strokeColor: "#fff", strokeWeight: 2, scale: 8 };
      const content = `<div style="min-width:190px;padding:8px;font-family:Arial,sans-serif"><strong>${camera.name}</strong><br/><small>${camera.camera_code}</small><br/><span>${camera.zone || "Location unavailable"}</span><br/><b>Status: ${camera.status}</b><br/><a href="/cameras/${camera.id}">Open live camera</a></div>`;
      let marker = markersRef.current.get(camera.id);
      let infoWindow = infoWindowsRef.current.get(camera.id);
      if (!marker) {
        marker = new Marker({ position: { lat: camera.latitude, lng: camera.longitude }, map: googleMapRef.current, title: camera.name, icon });
        infoWindow = new InfoWindow({ content });
        listenersRef.current.push(marker.addListener("click", () => {
          infoWindowsRef.current.forEach((window) => window.close());
          infoWindow?.open(googleMapRef.current, marker);
          onSelectCamera?.(camera);
        }));
        markersRef.current.set(camera.id, marker);
        infoWindowsRef.current.set(camera.id, infoWindow);
      } else {
        marker.setPosition({ lat: camera.latitude, lng: camera.longitude });
        marker.setIcon(icon);
        infoWindow?.setContent(content);
      }
    });
  }, [cameras, alerts, onSelectCamera]);

  useEffect(() => {
    if (!googleMapRef.current || !selectedCamera || typeof selectedCamera.latitude !== "number" || typeof selectedCamera.longitude !== "number") return;
    googleMapRef.current.panTo({ lat: selectedCamera.latitude, lng: selectedCamera.longitude });
    googleMapRef.current.setZoom(15);
  }, [selectedCamera]);

  return (
    <div className="relative h-full min-h-[400px] w-full rounded-lg bg-gray-800">
      <div ref={mapRef} className="h-full min-h-[400px] w-full rounded-lg" />
      {mapError && <div className="absolute inset-0 flex items-center justify-center bg-slate-900/95 p-6 text-center text-sm text-slate-300">{mapError}</div>}
    </div>
  );
}
