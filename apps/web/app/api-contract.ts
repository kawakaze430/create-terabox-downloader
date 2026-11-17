// Runtime guards for the small internal API, kept aligned with app/models.py.
// No upstream URLs or credentials are accepted by the public metadata contract.
export type ValidResult = { valid: true; hostname: string; normalized_url: string };
export type SharedFile = {
  file_id: string;
  name: string;
  kind: "file" | "folder";
  size_bytes: number | null;
  mime_type: string | null;
  qualities: string[];
  preview_available: boolean;
  download_available: boolean;
};
export type Capabilities = {
  metadata: boolean;
  preview: boolean;
  download: boolean;
  folders: boolean;
  batch: boolean;
  zip_download: boolean;
  quality_options: boolean;
};
export type ShareResolution = { provider: "terabox"; files: SharedFile[]; capabilities: Capabilities };

const invalidResponse = "The service returned an invalid response. Please try again.";
const capabilityKeys = ["metadata", "preview", "download", "folders", "batch", "zip_download", "quality_options"];
const fileKeys = ["file_id", "name", "kind", "size_bytes", "mime_type", "qualities", "preview_available", "download_available"];
const shareHosts = new Set(["terabox.com", "www.terabox.com", "teraboxapp.com", "www.teraboxapp.com", "1024terabox.com", "www.1024terabox.com", "terasharefile.com", "www.terasharefile.com"]);

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function keys(value: Record<string, unknown>, expected: string[]): boolean {
  return Object.keys(value).length === expected.length && expected.every(key => Object.hasOwn(value, key));
}

function boundedString(value: unknown, minimum: number, maximum: number): value is string {
  if (typeof value !== "string" || value.length > maximum * 2) return false;
  const length = [...value].length;
  return length >= minimum && length <= maximum;
}

function isFile(value: unknown): value is SharedFile {
  if (!record(value) || !keys(value, fileKeys)) return false;
  return boundedString(value.file_id, 1, 256) && !/[\x00-\x1f\x7f]/.test(value.file_id)
    && boundedString(value.name, 1, 512) && !/[\x00-\x1f\x7f/\\]/.test(value.name) && value.name !== "." && value.name !== ".."
    && (value.kind === "file" || value.kind === "folder")
    && (value.size_bytes === null || (typeof value.size_bytes === "number" && Number.isSafeInteger(value.size_bytes) && value.size_bytes >= 0))
    && (value.mime_type === null || boundedString(value.mime_type, 0, 128))
    && Array.isArray(value.qualities) && value.qualities.length <= 12
    && value.qualities.every(quality => boundedString(quality, 1, 32) && !/[\x00-\x1f]/.test(quality))
    && new Set(value.qualities).size === value.qualities.length
    && typeof value.preview_available === "boolean" && typeof value.download_available === "boolean";
}

function isCapabilities(value: unknown): value is Capabilities {
  return record(value) && keys(value, capabilityKeys) && capabilityKeys.every(key => typeof value[key] === "boolean");
}

export function parseValidationResult(value: unknown): ValidResult {
  if (!record(value) || value.valid !== true || (value.provider !== undefined && value.provider !== "terabox")
    || !boundedString(value.hostname, 1, 253) || !boundedString(value.normalized_url, 1, 2048)) throw new Error(invalidResponse);
  try {
    const url = new URL(value.normalized_url);
    if (url.protocol !== "https:" || url.username || url.password || url.port || url.hostname !== value.hostname || !shareHosts.has(url.hostname)) throw new Error();
  } catch {
    throw new Error(invalidResponse);
  }
  return { valid: true, hostname: value.hostname, normalized_url: value.normalized_url };
}

export function parseShareResolution(value: unknown): ShareResolution {
  if (!record(value) || !keys(value, ["provider", "files", "capabilities"]) || value.provider !== "terabox"
    || !Array.isArray(value.files) || value.files.length > 200 || !value.files.every(isFile)
    || !isCapabilities(value.capabilities)) throw new Error(invalidResponse);
  return { provider: "terabox", files: value.files, capabilities: value.capabilities };
}

export function apiErrorMessage(value: unknown, fallback: string): string {
  return record(value) && record(value.error) && boundedString(value.error.message, 1, 512)
    && !/[\x00-\x1f\x7f]/.test(value.error.message) ? value.error.message : fallback;
}

export async function readApiJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new Error(invalidResponse);
  }
}
