"use client";

import { useEffect, useRef, useState } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { getSvgUrl } from "@/lib/api";
import { sanitizeSvg } from "@/lib/sanitize";
import { useI18n } from "@/lib/i18n";

interface PlanViewerProps {
  jobId: string;
  svgContainerRef?: React.RefObject<HTMLDivElement | null>;
}

export function PlanViewer({ jobId, svgContainerRef }: PlanViewerProps) {
  const { t } = useI18n();
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const internalRef = useRef<HTMLDivElement>(null);
  const containerRef = svgContainerRef || internalRef;

  useEffect(() => {
    const fetchSvg = async () => {
      try {
        const res = await fetch(getSvgUrl(jobId));
        if (!res.ok) {
          setError(`${t("plan.svgError")} (${res.status})`);
          return;
        }
        const text = await res.text();
        setSvgContent(sanitizeSvg(text));
      } catch (e) {
        setError(e instanceof Error ? e.message : t("plan.networkError"));
      } finally {
        setLoading(false);
      }
    };

    fetchSvg();
  }, [jobId]);

  if (loading) {
    return (
      <div className="glass-card h-[70vh] min-h-[400px] max-h-[800px] flex flex-col" aria-busy="true">
        <div className="bg-gray-50/50 dark:bg-white/[0.02] border-b border-gray-200/60 dark:border-white/[0.06] px-4 py-2.5">
          <div className="h-4 w-48 bg-gray-200 dark:bg-white/[0.06] rounded-lg animate-pulse" />
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-lg space-y-4">
            <div className="aspect-[4/3] w-full bg-gray-100 dark:bg-white/[0.03] rounded-xl animate-pulse flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="animate-spin w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full" />
                <p className="text-gray-400 dark:text-gray-600 text-sm">{t("plan.loading")}</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="h-3 w-20 bg-gray-200 dark:bg-white/[0.06] rounded-lg animate-pulse" />
              <div className="h-3 w-16 bg-gray-200 dark:bg-white/[0.06] rounded-lg animate-pulse" />
              <div className="h-3 w-24 bg-gray-200 dark:bg-white/[0.06] rounded-lg animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !svgContent) {
    return (
      <div className="glass-card h-[70vh] min-h-[400px] max-h-[800px] flex items-center justify-center">
        <p className="text-red-500">{error || t("plan.svgError")}</p>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="bg-gray-50/50 dark:bg-white/[0.02] border-b border-gray-200/60 dark:border-white/[0.06] px-4 py-2.5 flex items-center justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {t("plan.zoomHint")}
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-600 hidden sm:inline font-mono">
          Ctrl+S: SVG &middot; Ctrl+P: PDF
        </span>
      </div>
      <TransformWrapper
        initialScale={1}
        minScale={0.1}
        maxScale={10}
        centerOnInit
      >
        <TransformComponent
          wrapperStyle={{ width: "100%", height: "70vh", minHeight: "400px", maxHeight: "800px" }}
          contentStyle={{ width: "100%", height: "100%" }}
        >
          <div
            ref={containerRef}
            dangerouslySetInnerHTML={{ __html: svgContent }}
            className="w-full h-full flex items-center justify-center"
          />
        </TransformComponent>
      </TransformWrapper>
    </div>
  );
}
