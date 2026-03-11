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
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <p className="text-xs text-gray-400">{t("metrics.unavailable")}</p>
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
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
        {t("metrics.title")}
      </h3>
      <div className="space-y-1.5">
        {steps.map((s) => (
          <div key={s.label} className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400">{s.label}</span>
            <span className="font-mono text-gray-700 dark:text-gray-200">{s.value}</span>
          </div>
        ))}
        <div className="border-t border-gray-100 dark:border-gray-600 pt-1.5 mt-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-gray-700 dark:text-gray-200">{t("metrics.total")}</span>
            <span className="font-mono text-red-600">{formatMs(metrics.total_pipeline_ms)}</span>
          </div>
        </div>
        <div className="border-t border-gray-100 dark:border-gray-600 pt-1.5 mt-1.5 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400">{t("metrics.walls")}</span>
            <span className="font-mono text-gray-700 dark:text-gray-200">{metrics.entities_walls}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400">{t("metrics.doors")}</span>
            <span className="font-mono text-gray-700 dark:text-gray-200">{metrics.entities_doors}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400">{t("metrics.rooms")}</span>
            <span className="font-mono text-gray-700 dark:text-gray-200">{metrics.rooms_detected} {t("metrics.detected")}, {metrics.rooms_classified} {t("metrics.classified")}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400">SVG</span>
            <span className="font-mono text-gray-700 dark:text-gray-200">{formatBytes(metrics.svg_size_bytes)}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400">PDF</span>
            <span className="font-mono text-gray-700 dark:text-gray-200">{formatBytes(metrics.pdf_size_bytes)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
