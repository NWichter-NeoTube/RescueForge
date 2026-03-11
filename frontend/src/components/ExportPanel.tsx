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
        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium flex items-center gap-1.5"
      >
        <Download size={16} />
        {t("export.button")}
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />

          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-1 z-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 min-w-[220px]">
            <p className="px-3 py-1.5 text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
              {t("export.floorPlan")}
            </p>
            <a
              href={getSvgUrl(jobId)}
              download="RescueForge-Orientierungsplan.svg"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {t("export.svgLabel")}
            </a>
            <a
              href={getPdfUrl(jobId)}
              download="RescueForge-Orientierungsplan.pdf"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {t("export.pdfLabel")}
            </a>

            <div className="border-t border-gray-100 dark:border-gray-700 my-1" />

            <p className="px-3 py-1.5 text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
              {t("export.supplementary")}
            </p>
            <a
              href={getCoverSheetUrl(jobId)}
              download="RescueForge-Deckblatt.svg"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {t("export.coverSvg")}
            </a>
            <a
              href={getSituationPlanUrl(jobId)}
              download="RescueForge-Situationsplan.svg"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {t("export.situationSvg")}
            </a>
          </div>
        </>
      )}
    </div>
  );
}
