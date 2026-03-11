"use client";

import { useEffect, useState } from "react";
import { updateRooms } from "@/lib/api";
import { useToast } from "@/components/Toast";
import { useI18n, TranslationKey } from "@/lib/i18n";

interface Room {
  id: number;
  room_type: string;
  label: string;
  area: number;
}

interface RoomEditorProps {
  jobId: string;
  onPlanRegenerated?: () => void;
}

const ROOM_TYPES: { value: string; key: TranslationKey }[] = [
  { value: "office", key: "room.office" },
  { value: "corridor", key: "room.corridor" },
  { value: "stairwell", key: "room.stairwell" },
  { value: "elevator", key: "room.elevator" },
  { value: "bathroom", key: "room.bathroom" },
  { value: "kitchen", key: "room.kitchen" },
  { value: "storage", key: "room.storage" },
  { value: "technical", key: "room.technical" },
  { value: "garage", key: "room.garage" },
  { value: "lobby", key: "room.lobby" },
  { value: "conference", key: "room.conference" },
  { value: "residential", key: "room.residential" },
  { value: "bedroom", key: "room.bedroom" },
  { value: "living_room", key: "room.living_room" },
  { value: "balcony", key: "room.balcony" },
  { value: "unknown", key: "room.unknown" },
];

// Use relative URLs — Next.js rewrites proxy /api/* to the backend service.
const API_BASE = "";

export function RoomEditor({ jobId, onPlanRegenerated }: RoomEditorProps) {
  const { t } = useI18n();
  const { addToast } = useToast();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [originalRooms, setOriginalRooms] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoadError(null);
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/data`);
        if (!res.ok) {
          setLoadError(`HTTP ${res.status}`);
          return;
        }
        const data = await res.json();
        const parsed = (data.rooms || []).map((r: any) => ({
          id: r.id,
          room_type: r.room_type,
          label: r.label || "",
          area: r.area || 0,
        }));
        setRooms(parsed);
        setOriginalRooms(JSON.stringify(parsed));
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [jobId]);

  const updateRoom = (id: number, field: string, value: string) => {
    setRooms((prev) => {
      const updated = prev.map((r) => {
        if (r.id !== id) return r;
        if (field === "room_type") {
          const typeInfo = ROOM_TYPES.find((rt) => rt.value === value);
          return { ...r, room_type: value, label: typeInfo ? t(typeInfo.key) : r.label };
        }
        return { ...r, [field]: value };
      });
      setHasChanges(JSON.stringify(updated) !== originalRooms);
      return updated;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateRooms(
        jobId,
        rooms.map((r) => ({ id: r.id, room_type: r.room_type, label: r.label })),
      );
      setOriginalRooms(JSON.stringify(rooms));
      setHasChanges(false);
      addToast(t("rooms.saved"), "success");
      onPlanRegenerated?.();
    } catch (e) {
      addToast(t("rooms.saveError"), "error");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">{t("rooms.loading")}</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-red-200 dark:border-red-800 p-4">
        <p className="text-sm text-red-600 dark:text-red-400">{t("rooms.saveError")}: {loadError}</p>
      </div>
    );
  }

  if (rooms.length === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200">
          {t("rooms.title")} ({rooms.length})
        </h3>
        {hasChanges && (
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {saving ? t("rooms.saving") : t("rooms.save")}
          </button>
        )}
      </div>
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {rooms.map((room) => (
          <div
            key={room.id}
            className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
          >
            <span className="w-6 h-6 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono text-gray-700 dark:text-gray-300">
              {room.id}
            </span>
            <select
              value={room.room_type}
              onChange={(e) => updateRoom(room.id, "room_type", e.target.value)}
              className="flex-1 border border-gray-200 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-gray-700 dark:text-gray-200"
            >
              {ROOM_TYPES.map((rt) => (
                <option key={rt.value} value={rt.value}>
                  {t(rt.key)}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={room.label}
              onChange={(e) => updateRoom(room.id, "label", e.target.value)}
              className="w-24 border border-gray-200 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-gray-700 dark:text-gray-200"
              placeholder="Label"
            />
            <span className="text-xs text-gray-400 w-16 text-right">
              {room.area > 0 ? `${(room.area / 1e6).toFixed(1)}m²` : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
