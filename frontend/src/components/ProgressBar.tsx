"use client";

import { JobStatus } from "@/lib/api";
import { useI18n, TranslationKey } from "@/lib/i18n";

interface ProgressBarProps {
  status: JobStatus;
}

const STEP_KEYS: Record<string, TranslationKey> = {
  pending: "progress.queued",
  converting: "progress.dwg",
  parsing: "progress.dxf",
  detecting_rooms: "progress.rooms",
  classifying: "progress.classify",
  generating: "progress.svg",
  exporting: "progress.pdf",
  completed: "progress.done",
  failed: "progress.error",
};

export function ProgressBar({ status }: ProgressBarProps) {
  const { t } = useI18n();
  const progress = Math.max(status.progress * 100, 5);
  const key = STEP_KEYS[status.status];
  const label = key ? t(key) : status.message || t("progress.processing");

  return (
    <div className="glass-card p-5" role="progressbar" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{label}</span>
        <span className="text-sm tabular-nums text-gray-400 dark:text-gray-500 font-mono">{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-gray-100 dark:bg-white/[0.06] rounded-full h-2 overflow-hidden">
        <div
          className="bg-gradient-to-r from-red-500 to-red-600 h-2 rounded-full transition-all duration-700 ease-out relative"
          style={{ width: `${progress}%` }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse-slow" />
        </div>
      </div>
    </div>
  );
}
