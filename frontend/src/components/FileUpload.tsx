"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useI18n } from "@/lib/i18n";
import { Upload } from "lucide-react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onMultiFileSelect?: (files: File[]) => void;
  disabled?: boolean;
  multiple?: boolean;
}

export function FileUpload({ onFileSelect, onMultiFileSelect, disabled, multiple }: FileUploadProps) {
  const { t } = useI18n();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0 && !disabled) {
        if (multiple && onMultiFileSelect && acceptedFiles.length > 1) {
          onMultiFileSelect(acceptedFiles);
        } else {
          onFileSelect(acceptedFiles[0]);
        }
      }
    },
    [onFileSelect, onMultiFileSelect, disabled, multiple],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/dxf": [".dxf"],
      "application/dwg": [".dwg"],
      "application/acad": [".dwg"],
      "application/x-autocad": [".dwg", ".dxf"],
    },
    maxFiles: multiple ? 10 : 1,
    disabled,
    multiple,
  });

  return (
    <div
      {...getRootProps()}
      data-testid="file-upload"
      role="button"
      aria-label={t("upload.dropzone.aria")}
      tabIndex={0}
      className={`
        group relative rounded-2xl p-12 text-center cursor-pointer transition-all duration-300
        border-2 border-dashed
        ${isDragActive
          ? "border-red-500 bg-red-500/5 dark:bg-red-500/10 scale-[1.01]"
          : "border-gray-300/60 dark:border-white/[0.08] bg-white/60 dark:bg-white/[0.02] hover:border-red-400/60 dark:hover:border-red-500/30 hover:bg-red-50/30 dark:hover:bg-red-500/5"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center gap-4">
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 ${
          isDragActive
            ? "bg-red-500/10 dark:bg-red-500/20 scale-110"
            : "bg-gray-100 dark:bg-white/[0.06] group-hover:bg-red-500/10 dark:group-hover:bg-red-500/10"
        }`}>
          <Upload size={24} className={`transition-all duration-300 ${
            isDragActive
              ? "text-red-500 -translate-y-0.5"
              : "text-gray-400 dark:text-gray-500 group-hover:text-red-500"
          }`} />
        </div>

        {isDragActive ? (
          <p className="text-red-600 dark:text-red-400 font-medium text-lg">
            {t("upload.dropzone.active")}
          </p>
        ) : (
          <>
            <p className="text-gray-700 dark:text-gray-200 font-medium text-lg">
              {t("upload.dropzone.text")}
            </p>
            <p className="text-sm text-gray-400 dark:text-gray-500">
              {t("upload.dropzone.hint")}
              {multiple && <span className="text-gray-400 dark:text-gray-600">{t("upload.dropzone.multi")}</span>}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
