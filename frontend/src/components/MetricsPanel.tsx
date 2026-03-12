"use client";

import { useEffect, useState } from "react";
import { getMetrics, PipelineMetrics } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

interface MetricsPanelProps {
  jobId: string;
}

function formatMs(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${bytes}B`;
}

export function MetricsPanel({ jobId }: MetricsPanelProps) {
  const { t } = useI18n();
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getMetrics(jobId)
      .then(setMetrics)
      .catch(() => setError(true));
  }, [jobId]);

  if (error) {
    return (
      <div className="glass-card p-4">
        <p className="text-xs text-gray-400 dark:text-gray-600">{t("metrics.unavailable")}</p>
      </div>
    );
  }

  if (!metrics) return null;

  const steps = [
    { label: t("metrics.dxfParsing"), value: formatMs(metrics.dxf_parsing_ms) },
    { label: t("metrics.roomDetection"), value: formatMs(metrics.room_detection_ms) },
    { label: t("metrics.aiClassification"), value: formatMs(metrics.room_classification_ms) },
    { label: t("metrics.svgGeneration"), value: formatMs(metrics.svg_generation_ms) },
    { label: t("metrics.pdfExport"), value: formatMs(metrics.pdf_export_ms) },
  ];

  return (
    <div className="glass-card p-4">
      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
        {t("metrics.title")}
      </h3>
      <div className="space-y-1.5">
        {steps.map((s) => (
          <div key={s.label} className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-500">{s.label}</span>
            <span className="font-mono tabular-nums text-gray-700 dark:text-gray-300">{s.value}</span>
          </div>
        ))}
        <div className="border-t border-gray-100 dark:border-white/[0.06] pt-1.5 mt-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-gray-700 dark:text-gray-200">{t("metrics.total")}</span>
            <span className="font-mono tabular-nums text-red-500">{formatMs(metrics.total_pipeline_ms)}</span>
          </div>
        </div>
        <div className="border-t border-gray-100 dark:border-white/[0.06] pt-1.5 mt-1.5 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-500">{t("metrics.walls")}</span>
            <span className="font-mono tabular-nums text-gray-700 dark:text-gray-300">{metrics.entities_walls}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-500">{t("metrics.doors")}</span>
            <span className="font-mono tabular-nums text-gray-700 dark:text-gray-300">{metrics.entities_doors}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-500">{t("metrics.rooms")}</span>
            <span className="font-mono tabular-nums text-gray-700 dark:text-gray-300">{metrics.rooms_detected} {t("metrics.detected")}, {metrics.rooms_classified} {t("metrics.classified")}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-500">SVG</span>
            <span className="font-mono tabular-nums text-gray-700 dark:text-gray-300">{formatBytes(metrics.svg_size_bytes)}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-500">PDF</span>
            <span className="font-mono tabular-nums text-gray-700 dark:text-gray-300">{formatBytes(metrics.pdf_size_bytes)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
