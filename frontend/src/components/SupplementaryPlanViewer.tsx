"use client";

import { useEffect, useState } from "react";
import { sanitizeSvg } from "@/lib/sanitize";
import { useI18n } from "@/lib/i18n";

interface SupplementaryPlanViewerProps {
  url: string;
  title: string;
  description: string;
}

export function SupplementaryPlanViewer({
  url,
  title,
  description,
}: SupplementaryPlanViewerProps) {
  const { t } = useI18n();
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const text = await res.text();
        setSvgContent(sanitizeSvg(text));
      } catch (e) {
        setError(
          e instanceof Error ? e.message : t("supp.loadFailed"),
        );
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [url]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
        <div className="animate-spin w-8 h-8 border-2 border-red-600 border-t-transparent rounded-full mx-auto mb-3" />
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          {t("supp.loading", { title })}
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-red-200 dark:border-red-800 p-8 text-center">
        <p className="text-red-600 dark:text-red-400 font-medium mb-1">
          {t("supp.error", { title })}
        </p>
        <p className="text-gray-500 dark:text-gray-400 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600 px-4 py-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200">
            {title}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {description}
          </p>
        </div>
        <a
          href={url}
          download
          className="px-3 py-1.5 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-500 transition-colors text-xs font-medium"
        >
          {t("supp.download")}
        </a>
      </div>
      <div className="p-4">
        {svgContent ? (
          <div
            dangerouslySetInnerHTML={{ __html: svgContent }}
            className="w-full [&>svg]:w-full [&>svg]:h-auto [&>svg]:max-h-[700px] [&>svg]:mx-auto"
          />
        ) : (
          <p className="text-gray-400 text-sm text-center py-8">
            {t("supp.noPreview")}
          </p>
        )}
      </div>
    </div>
  );
}
