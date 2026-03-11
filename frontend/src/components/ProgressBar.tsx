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
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6" role="progressbar" aria-valuenow={Math.round(progress)} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{label}</span>
        <span className="text-sm text-gray-500 dark:text-gray-400">{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5">
        <div
          className="bg-red-600 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
