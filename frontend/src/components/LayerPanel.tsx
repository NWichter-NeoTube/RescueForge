"use client";

import { useState } from "react";
import { useI18n, TranslationKey } from "@/lib/i18n";

interface LayerPanelProps {
  svgContainerRef?: React.RefObject<HTMLDivElement | null>;
}

const LAYERS: { id: string; key: TranslationKey; defaultVisible: boolean; color: string }[] = [
  { id: "rooms", key: "layer.rooms", defaultVisible: true, color: "#E0E0E0" },
  { id: "walls", key: "layer.walls", defaultVisible: true, color: "#000000" },
  { id: "doors", key: "layer.doors", defaultVisible: true, color: "#8B4513" },
  { id: "stairs", key: "layer.stairs", defaultVisible: true, color: "#006400" },
];

export function LayerPanel({ svgContainerRef }: LayerPanelProps) {
  const { t } = useI18n();
  const [visibility, setVisibility] = useState<Record<string, boolean>>(
    Object.fromEntries(LAYERS.map((l) => [l.id, l.defaultVisible])),
  );

  const toggleLayer = (layerId: string) => {
    const newVisible = !visibility[layerId];
    setVisibility((prev) => ({ ...prev, [layerId]: newVisible }));

    // Toggle SVG group visibility
    if (svgContainerRef?.current) {
      const svgEl = svgContainerRef.current.querySelector("svg");
      if (svgEl) {
        const group = svgEl.querySelector(`#${layerId}`);
        if (group) {
          (group as SVGElement).style.display = newVisible ? "" : "none";
        }
      }
    }
  };

  return (
    <div className="glass-card p-4">
      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">{t("layer.title")}</h3>
      <div className="space-y-1.5">
        {LAYERS.map((layer) => (
          <label
            key={layer.id}
            className="flex items-center gap-2.5 cursor-pointer group px-2 py-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors"
          >
            <input
              type="checkbox"
              checked={visibility[layer.id]}
              onChange={() => toggleLayer(layer.id)}
              className="rounded border-gray-300 dark:border-gray-600 text-red-600 focus:ring-red-500 focus:ring-offset-0 dark:bg-white/[0.06]"
            />
            <span
              className="w-3 h-3 rounded-sm border border-gray-200 dark:border-gray-700 shrink-0"
              style={{ backgroundColor: layer.color }}
            />
            <span className="text-sm text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200 transition-colors">
              {t(layer.key)}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}
