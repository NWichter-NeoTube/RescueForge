"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { useToast } from "@/components/Toast";
import { useI18n } from "@/lib/i18n";
import { FileUpload } from "@/components/FileUpload";
import { ProgressBar } from "@/components/ProgressBar";
import { PlanViewer } from "@/components/PlanViewer";
import { ExportPanel } from "@/components/ExportPanel";
import { LayerPanel } from "@/components/LayerPanel";
import { RoomEditor } from "@/components/RoomEditor";
import { MetricsPanel } from "@/components/MetricsPanel";
import { ComparisonView } from "@/components/ComparisonView";
import { SupplementaryPlanViewer } from "@/components/SupplementaryPlanViewer";
import { Logo } from "@/components/Logo";
import {
  uploadFile,
  uploadBatch,
  watchJobProgress,
  getCoverSheetUrl,
  getSituationPlanUrl,
  getSvgUrl,
  getPdfUrl,
  JobStatus,
  BatchUploadResponse,
} from "@/lib/api";
import {
  Sun,
  Moon,
  Layers,
  Brain,
  ShieldCheck,
  Plus,
  Globe,
} from "lucide-react";

export default function Home() {
  const { addToast } = useToast();
  const { t, locale, setLocale } = useI18n();
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("rescueforge-dark");
      // Default to dark if not set
      return stored === null ? true : stored === "true";
    }
    return true;
  });
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [planVersion, setPlanVersion] = useState(0);
  const [viewMode, setViewMode] = useState<"plan" | "compare" | "cover" | "situation">("plan");
  const [batchJobs, setBatchJobs] = useState<
    { job_id: string; filename: string; status: JobStatus | null }[]
  >([]);
  const svgContainerRef = useRef<HTMLDivElement>(null);

  const isComplete = status?.status === "completed";

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("rescueforge-dark", String(darkMode));
  }, [darkMode]);

  // Keyboard shortcuts: Ctrl+S -> SVG download, Ctrl+P -> PDF download
  useEffect(() => {
    if (!isComplete || !jobId) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const mod = e.ctrlKey || e.metaKey;
      if (!mod) return;

      if (e.key === "s") {
        e.preventDefault();
        window.open(getSvgUrl(jobId), "_blank");
        addToast(t("shortcut.svgDownload"), "success");
      } else if (e.key === "p") {
        e.preventDefault();
        window.open(getPdfUrl(jobId), "_blank");
        addToast(t("shortcut.pdfDownload"), "success");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isComplete, jobId, addToast, t]);

  const handlePlanRegenerated = useCallback(() => {
    setPlanVersion((v) => v + 1);
  }, []);

  const handleFileUpload = async (file: File) => {
    setError(null);
    setIsProcessing(true);

    try {
      const result = await uploadFile(file, locale);
      setJobId(result.job_id);

      const finalStatus = await watchJobProgress(result.job_id, (s) => {
        setStatus(s);
      });

      setStatus(finalStatus);

      if (finalStatus.status === "failed") {
        setError(finalStatus.message || t("upload.failed"));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("upload.failed"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleMultiFileUpload = async (files: File[]) => {
    setError(null);
    setIsProcessing(true);

    try {
      const batch: BatchUploadResponse = await uploadBatch(files, locale);
      setBatchJobs(
        batch.jobs.map((j) => ({ ...j, status: null })),
      );

      const promises = batch.jobs.map((job, idx) =>
        watchJobProgress(job.job_id, (s) => {
          setBatchJobs((prev) =>
            prev.map((bj, i) => (i === idx ? { ...bj, status: s } : bj)),
          );
        }),
      );

      const results = await Promise.all(promises);
      const first = results.find((r) => r.status === "completed");
      if (first) {
        setJobId(first.job_id);
        setStatus(first);
      } else {
        setError(t("upload.allFailed"));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("upload.batchFailed"));
    } finally {
      setIsProcessing(false);
    }
  };

  const features = [
    {
      icon: Layers,
      title: t("feature.cleanup.title"),
      desc: t("feature.cleanup.desc"),
      gradient: "from-blue-500 to-cyan-400",
      iconBg: "bg-blue-500/10 dark:bg-blue-500/20",
      iconColor: "text-blue-500",
    },
    {
      icon: Brain,
      title: t("feature.ai.title"),
      desc: t("feature.ai.desc"),
      gradient: "from-purple-500 to-pink-400",
      iconBg: "bg-purple-500/10 dark:bg-purple-500/20",
      iconColor: "text-purple-500",
    },
    {
      icon: ShieldCheck,
      title: t("feature.fks.title"),
      desc: t("feature.fks.desc"),
      gradient: "from-red-500 to-orange-400",
      iconBg: "bg-red-500/10 dark:bg-red-500/20",
      iconColor: "text-red-500",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200/60 dark:border-white/[0.06]">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <Logo size={36} />
            <div>
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white tracking-tight">
                RescueForge
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {t("app.subtitle")}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            {/* Language toggle */}
            <button
              onClick={() => setLocale(locale === "en" ? "de" : "en")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-all text-sm"
              aria-label="Switch language"
              title={locale === "en" ? "Deutsch" : "English"}
            >
              <Globe size={15} />
              <span className="uppercase font-medium text-xs">{locale}</span>
            </button>
            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkMode((d) => !d)}
              className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/[0.06] transition-all"
              aria-label={darkMode ? t("darkMode.light") : t("darkMode.dark")}
              title={darkMode ? "Light Mode" : "Dark Mode"}
            >
              {darkMode ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {!isComplete ? (
          <div className="animate-fade-in">
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-8 items-start">
              {/* Left: Upload area */}
              <div>
                <div className="mb-8">
                  <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-3 tracking-tight">
                    {t("upload.title")}
                  </h2>
                  <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed max-w-xl">
                    {t("upload.description")}
                  </p>
                  <p className="text-gray-400 dark:text-gray-500 text-xs mt-2">
                    {locale === "de"
                      ? "Ausgabe erfolgt normkonform nach DIN 14095 und der Schweizer FKS-Richtlinie."
                      : "Output is generated in compliance with DIN 14095 and the Swiss FKS guideline."}
                  </p>
                </div>

                <FileUpload
                  onFileSelect={handleFileUpload}
                  onMultiFileSelect={handleMultiFileUpload}
                  disabled={isProcessing}
                  multiple
                />

                {isProcessing && status && (
                  <div className="mt-6">
                    <ProgressBar status={status} />
                  </div>
                )}

                {isProcessing && batchJobs.length > 0 && (
                  <div className="mt-6 space-y-2">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      {t("progress.batch")} ({batchJobs.filter((j) => j.status?.status === "completed").length}/{batchJobs.length})
                    </p>
                    {batchJobs.map((job) => (
                      <div key={job.job_id} className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 dark:text-gray-400 truncate w-40">{job.filename}</span>
                        <div className="flex-1 bg-gray-100 dark:bg-white/[0.06] rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full transition-all duration-500 ${
                              job.status?.status === "completed"
                                ? "bg-emerald-500"
                                : job.status?.status === "failed"
                                  ? "bg-red-500"
                                  : "bg-red-400"
                            }`}
                            style={{ width: `${(job.status?.progress ?? 0) * 100}%` }}
                          />
                        </div>
                        <span className="text-gray-400 w-12 text-right">
                          {Math.round((job.status?.progress ?? 0) * 100)}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {error && (
                  <div className="mt-6 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl p-4 flex items-start justify-between animate-slide-up">
                    <p className="text-red-700 dark:text-red-400 text-sm">{error}</p>
                    <button
                      onClick={() => setError(null)}
                      className="ml-3 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-lg leading-none"
                      aria-label={t("error.close")}
                    >
                      &times;
                    </button>
                  </div>
                )}
              </div>

              {/* Right: Feature cards */}
              <div className="space-y-3 lg:pt-14">
                {features.map((f) => (
                  <div
                    key={f.title}
                    className="group flex items-start gap-3.5 p-4 rounded-2xl glass-card hover:border-gray-300/60 dark:hover:border-white/[0.12] transition-all duration-300"
                  >
                    <div className={`w-9 h-9 rounded-lg ${f.iconBg} flex items-center justify-center shrink-0`}>
                      <f.icon size={18} className={f.iconColor} />
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-0.5">
                        {f.title}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-500 leading-relaxed">{f.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
              <div className="flex items-center gap-4 min-w-0">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight whitespace-nowrap">
                  {t("plan.title")}
                </h2>
                <div className="flex bg-gray-100 dark:bg-white/[0.06] rounded-xl p-1 overflow-x-auto border border-transparent dark:border-white/[0.06]">
                  {([
                    { key: "plan", label: t("plan.tab.floor") },
                    { key: "cover", label: t("plan.tab.cover") },
                    { key: "situation", label: t("plan.tab.situation") },
                    { key: "compare", label: t("plan.tab.compare") },
                  ] as const).map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setViewMode(tab.key)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                        viewMode === tab.key
                          ? "bg-white dark:bg-white/[0.1] text-gray-900 dark:text-white shadow-sm"
                          : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 items-center">
                {batchJobs.length > 1 && (
                  <select
                    value={jobId!}
                    onChange={(e) => {
                      setJobId(e.target.value);
                      setPlanVersion((v) => v + 1);
                    }}
                    aria-label={t("plan.selectFloor")}
                    className="px-3 py-2 bg-gray-100 dark:bg-white/[0.06] text-gray-700 dark:text-gray-200 rounded-lg text-sm border border-transparent dark:border-white/[0.06]"
                  >
                    {batchJobs
                      .filter((j) => j.status?.status === "completed")
                      .map((j) => (
                        <option key={j.job_id} value={j.job_id}>
                          {j.filename}
                        </option>
                      ))}
                  </select>
                )}
                <ExportPanel jobId={jobId!} />
                <button
                  onClick={() => {
                    setJobId(null);
                    setStatus(null);
                    setError(null);
                    setViewMode("plan");
                    setBatchJobs([]);
                  }}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-white/[0.06] text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/[0.1] border border-transparent dark:border-white/[0.06] transition-all"
                  aria-label={t("plan.newPlan.aria")}
                >
                  <Plus size={16} />
                  {t("plan.newPlan")}
                </button>
              </div>
            </div>

            {viewMode === "compare" ? (
              <ComparisonView jobId={jobId!} />
            ) : viewMode === "cover" ? (
              <SupplementaryPlanViewer
                url={getCoverSheetUrl(jobId!)}
                title={t("cover.title")}
                description={t("cover.desc")}
              />
            ) : viewMode === "situation" ? (
              <SupplementaryPlanViewer
                url={getSituationPlanUrl(jobId!)}
                title={t("situation.title")}
                description={t("situation.desc")}
              />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-[1fr_260px] gap-6">
                <PlanViewer jobId={jobId!} svgContainerRef={svgContainerRef} key={`plan-${planVersion}`} />
                <div className="space-y-4">
                  <LayerPanel svgContainerRef={svgContainerRef} />
                  <RoomEditor jobId={jobId!} onPlanRegenerated={handlePlanRegenerated} />
                  <MetricsPanel jobId={jobId!} />
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
