// Use relative URLs — Next.js rewrites proxy /api/* to the backend service.
// This means no backend port needs to be exposed to the browser.
const API_BASE = "";
const WS_BASE =
  typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
    : "";

export interface UploadResponse {
  job_id: string;
  filename: string;
  status: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  message: string;
  result_svg: string | null;
  result_pdf: string | null;
}

export async function uploadFile(file: File, language: string = "en"): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload?language=${language}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }

  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch job status");
  }

  return res.json();
}

export async function pollJobStatus(
  jobId: string,
  onUpdate: (status: JobStatus) => void,
  intervalMs = 2000,
): Promise<JobStatus> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getJobStatus(jobId);
        onUpdate(status);

        if (status.status === "completed" || status.status === "failed") {
          resolve(status);
        } else {
          setTimeout(poll, intervalMs);
        }
      } catch (e) {
        reject(e);
      }
    };

    poll();
  });
}

/**
 * Watch job progress via WebSocket with automatic fallback to HTTP polling.
 */
export function watchJobProgress(
  jobId: string,
  onUpdate: (status: JobStatus) => void,
): Promise<JobStatus> {
  return new Promise((resolve, reject) => {
    let resolved = false;

    try {
      const ws = new WebSocket(`${WS_BASE}/api/ws/${jobId}`);

      const fallbackTimeout = setTimeout(() => {
        // If WebSocket doesn't connect in 3s, fall back to polling
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close();
          pollJobStatus(jobId, onUpdate).then(resolve).catch(reject);
        }
      }, 3000);

      ws.onopen = () => {
        clearTimeout(fallbackTimeout);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "progress") {
          onUpdate({
            job_id: jobId,
            status: data.status || data.step,
            progress: data.progress,
            message: data.message,
            result_svg: null,
            result_pdf: null,
          });
        } else if (data.type === "complete") {
          const finalStatus: JobStatus = {
            job_id: jobId,
            status: "completed",
            progress: 1.0,
            message: "Processing completed",
            result_svg: data.svg_url,
            result_pdf: data.pdf_url,
          };
          onUpdate(finalStatus);
          resolved = true;
          ws.close();
          resolve(finalStatus);
        } else if (data.type === "error") {
          const errorStatus: JobStatus = {
            job_id: jobId,
            status: "failed",
            progress: 0,
            message: data.message || "Processing failed",
            result_svg: null,
            result_pdf: null,
          };
          onUpdate(errorStatus);
          resolved = true;
          ws.close();
          resolve(errorStatus);
        }
      };

      ws.onerror = () => {
        clearTimeout(fallbackTimeout);
        if (!resolved) {
          // Fallback to polling
          ws.close();
          pollJobStatus(jobId, onUpdate).then(resolve).catch(reject);
        }
      };

      ws.onclose = () => {
        clearTimeout(fallbackTimeout);
        if (!resolved) {
          // Connection lost - fallback to polling
          pollJobStatus(jobId, onUpdate).then(resolve).catch(reject);
        }
      };
    } catch {
      // WebSocket not supported - fallback to polling
      pollJobStatus(jobId, onUpdate).then(resolve).catch(reject);
    }
  });
}

export function getSvgUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/svg`;
}

export function getPdfUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/pdf`;
}

export function getCoverSheetUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/cover-sheet`;
}

export function getSituationPlanUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/situation-plan`;
}

export interface PipelineMetrics {
  dwg_conversion_ms: number;
  dxf_parsing_ms: number;
  entities_walls: number;
  entities_doors: number;
  entities_stairs: number;
  room_detection_ms: number;
  rooms_detected: number;
  room_classification_ms: number;
  rooms_classified: number;
  svg_generation_ms: number;
  svg_size_bytes: number;
  pdf_export_ms: number;
  pdf_size_bytes: number;
  total_pipeline_ms: number;
}

export async function getMetrics(jobId: string): Promise<PipelineMetrics> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function updateRooms(
  jobId: string,
  rooms: { id: number; room_type: string; label: string }[],
  language: string = "en",
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}/rooms?language=${language}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rooms),
  });
  if (!res.ok) throw new Error("Failed to update rooms");
}

export interface BatchUploadResponse {
  batch_id: string;
  jobs: { job_id: string; filename: string }[];
  count: number;
}

export async function uploadBatch(
  files: File[],
  language: string = "en",
): Promise<BatchUploadResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const res = await fetch(`${API_BASE}/api/upload/batch?language=${language}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Batch upload failed" }));
    throw new Error(err.detail || "Batch upload failed");
  }

  return res.json();
}

export function getComplianceDocUrl(jobId: string): string {
  return `${API_BASE}/api/jobs/${jobId}/compliance`;
}
