"use client";

import { useState } from "react";
import { getSvgUrl, getPdfUrl, getCoverSheetUrl, getSituationPlanUrl } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Download } from "lucide-react";

interface ExportPanelProps {
  jobId: string;
}

export function ExportPanel({ jobId }: ExportPanelProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative" role="menu">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="true"
        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-all text-sm font-medium flex items-center gap-1.5 shadow-sm shadow-red-600/20 hover:shadow-md hover:shadow-red-600/25"
      >
        <Download size={15} />
        {t("export.button")}
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />

          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-2 z-20 bg-white dark:bg-gray-900 border border-gray-200/60 dark:border-white/[0.08] rounded-xl shadow-xl dark:shadow-2xl py-1.5 min-w-[220px] backdrop-blur-xl animate-fade-in">
            <p className="px-3 py-1.5 text-[10px] font-semibold text-gray-400 dark:text-gray-600 uppercase tracking-wider">
              {t("export.floorPlan")}
            </p>
            <a
              href={getSvgUrl(jobId)}
              download="RescueForge-Orientierungsplan.svg"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors rounded-lg mx-1"
            >
              {t("export.svgLabel")}
            </a>
            <a
              href={getPdfUrl(jobId)}
              download="RescueForge-Orientierungsplan.pdf"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors rounded-lg mx-1"
            >
              {t("export.pdfLabel")}
            </a>

            <div className="border-t border-gray-100 dark:border-white/[0.06] my-1.5" />

            <p className="px-3 py-1.5 text-[10px] font-semibold text-gray-400 dark:text-gray-600 uppercase tracking-wider">
              {t("export.supplementary")}
            </p>
            <a
              href={getCoverSheetUrl(jobId)}
              download="RescueForge-Deckblatt.svg"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors rounded-lg mx-1"
            >
              {t("export.coverSvg")}
            </a>
            <a
              href={getSituationPlanUrl(jobId)}
              download="RescueForge-Situationsplan.svg"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/[0.04] transition-colors rounded-lg mx-1"
            >
              {t("export.situationSvg")}
            </a>
          </div>
        </>
      )}
    </div>
  );
}
