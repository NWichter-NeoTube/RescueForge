"use client";

import { useEffect, useState } from "react";
import { getSvgUrl } from "@/lib/api";
import { sanitizeSvg } from "@/lib/sanitize";
import { useI18n } from "@/lib/i18n";

// Use relative URLs — Next.js rewrites proxy /api/* to the backend service.
const API_BASE = "";

interface ComparisonViewProps {
  jobId: string;
}

export function ComparisonView({ jobId }: ComparisonViewProps) {
  const { t } = useI18n();
  const [originalSvg, setOriginalSvg] = useState<string | null>(null);
  const [generatedSvg, setGeneratedSvg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [origRes, genRes] = await Promise.all([
          fetch(`${API_BASE}/api/jobs/${jobId}/original-svg`),
          fetch(getSvgUrl(jobId)),
        ]);

        if (origRes.ok) setOriginalSvg(sanitizeSvg(await origRes.text()));
        if (genRes.ok) setGeneratedSvg(sanitizeSvg(await genRes.text()));
      } catch (e) {
        console.error("Failed to load comparison:", e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [jobId]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center" aria-busy="true">
        <div className="animate-spin w-8 h-8 border-2 border-red-600 border-t-transparent rounded-full mx-auto mb-3" />
        <p className="text-gray-500 dark:text-gray-400">{t("compare.loading")}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="bg-gray-50 dark:bg-gray-700 border-b dark:border-gray-600 px-4 py-2">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{t("compare.original")}</span>
        </div>
        <div className="p-2 h-[500px] flex items-center justify-center">
          {originalSvg ? (
            <div
              dangerouslySetInnerHTML={{ __html: originalSvg }}
              className="w-full h-full [&>svg]:w-full [&>svg]:h-full [&>svg]:object-contain"
            />
          ) : (
            <p className="text-gray-400 text-sm">{t("compare.unavailable")}</p>
          )}
        </div>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="bg-red-50 dark:bg-red-900/30 border-b dark:border-gray-600 px-4 py-2">
          <span className="text-sm font-medium text-red-700 dark:text-red-400">{t("compare.generated")}</span>
        </div>
        <div className="p-2 h-[500px] flex items-center justify-center">
          {generatedSvg ? (
            <div
              dangerouslySetInnerHTML={{ __html: generatedSvg }}
              className="w-full h-full [&>svg]:w-full [&>svg]:h-full [&>svg]:object-contain"
            />
          ) : (
            <p className="text-gray-400 text-sm">{t("compare.unavailable")}</p>
          )}
        </div>
      </div>
    </div>
  );
}
