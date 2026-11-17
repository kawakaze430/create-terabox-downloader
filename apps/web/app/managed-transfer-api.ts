const maxFileBytes = 16 * 1024 * 1024;
const maxJsonBytes = 32 * 1024;
const digestPattern = /^[a-f0-9]{64}$/;
const filenamePattern = /^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$/;
const jobIdPattern = /^[a-f0-9]{32}$/;
const invalidResponse = "The transfer service sent an invalid response.";

export const transferStatuses = {
  queued: "Waiting for transfer",
  running: "Transferring file",
  completed: "Transfer verified by the service",
  cancelled: "Transfer cancelled",
  failed: "Transfer failed",
};

export type ManagedSource = {
  source_id: string;
  name: string;
  size_bytes: number;
  sha256: string;
};

export type ManagedJob = {
  id: string;
  state: keyof typeof transferStatuses;
  bytes_written: number;
  total_bytes: number;
};

export type ManagedSession = {
  token: string;
  expiresAt: number;
  sources: ManagedSource[];
};

export class ManagedRequestError extends Error {
  constructor(readonly status: number) {
    super(status === 429 || status === 503
      ? "The transfer service is busy. Try again shortly."
      : "The transfer service could not complete the request.");
  }
}

export function managedApi(configured: string | undefined, pageOrigin: string): string | null {
  if (configured === undefined) return null;
  const input = configured === "" ? pageOrigin : configured;
  try {
    const url = new URL(input);
    if (input !== url.origin && input !== url.origin + "/") return null;
    const local = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
    if (url.protocol === "https:" || (url.protocol === "http:" && local)) {
      return url.origin + "/api/v1/transfers";
    }
  } catch {
    return null;
  }
  return null;
}

function object(value: unknown): Record<string, unknown> {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) return value as Record<string, unknown>;
  throw new Error(invalidResponse);
}

function parseSession(value: unknown) {
  const { token, expires_in } = object(value);
  if (typeof token !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(token)
    || typeof expires_in !== "number" || !Number.isInteger(expires_in) || expires_in < 1 || expires_in > 3600) {
    throw new Error(invalidResponse);
  }
  return { token, expiresAt: Date.now() + expires_in * 1000 };
}

function parseSources(value: unknown): ManagedSource[] {
  const { sources } = object(value);
  if (!Array.isArray(sources) || sources.length > 32) throw new Error(invalidResponse);
  const ids = new Set<string>();
  return sources.map(item => {
    const { source_id, name, size_bytes, sha256 } = object(item);
    if (typeof source_id !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(source_id) || ids.has(source_id)
      || typeof name !== "string" || !filenamePattern.test(name)
      || typeof size_bytes !== "number" || !Number.isInteger(size_bytes) || size_bytes < 0 || size_bytes > maxFileBytes
      || typeof sha256 !== "string" || !digestPattern.test(sha256)) throw new Error(invalidResponse);
    ids.add(source_id);
    return { source_id, name, size_bytes, sha256 };
  });
}

export function parseManagedJob(value: unknown, source: ManagedSource, expectedId?: string): ManagedJob {
  const { id, state, bytes_written, total_bytes, sha256 } = object(value);
  if (typeof id !== "string" || !jobIdPattern.test(id) || (expectedId !== undefined && id !== expectedId)
    || typeof state !== "string" || !Object.hasOwn(transferStatuses, state) || total_bytes !== source.size_bytes
    || typeof bytes_written !== "number" || !Number.isInteger(bytes_written)
    || bytes_written < 0 || bytes_written > total_bytes) throw new Error(invalidResponse);
  if (state === "completed" ? sha256 !== source.sha256 || bytes_written !== total_bytes : sha256 !== null) {
    throw new Error(invalidResponse);
  }
  return { id, state: state as ManagedJob["state"], bytes_written, total_bytes };
}

type RequestOptions = {
  token?: string;
  body?: object;
  signal?: AbortSignal;
  timeoutMs?: number;
};

async function request(api: string, path: string, { token, body, signal, timeoutMs = 8000 }: RequestOptions) {
  const headers = new Headers();
  if (token) headers.set("Authorization", "Bearer " + token);
  if (body !== undefined) headers.set("Content-Type", "application/json");
  const timeout = AbortSignal.timeout(timeoutMs);
  const response = await fetch(api + path, {
    headers,
    method: body === undefined ? "GET" : "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "omit",
    redirect: "error",
    cache: "no-store",
    referrerPolicy: "no-referrer",
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!response.ok) {
    void response.body?.cancel().catch(() => {});
    throw new ManagedRequestError(response.status);
  }
  return response;
}

async function readBounded(response: Response, maximum: number) {
  const bytes = new Uint8Array(maximum);
  if (!response.body) return bytes.subarray(0, 0);
  const reader = response.body.getReader();
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) return bytes.subarray(0, size);
      if (value.byteLength > maximum - size) throw new Error(invalidResponse);
      bytes.set(value, size);
      size += value.byteLength;
    }
  } finally {
    void reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export async function managedJson(api: string, path: string, options: RequestOptions): Promise<unknown> {
  const response = await request(api, path, options);
  const bytes = await readBounded(response, maxJsonBytes);
  return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)) as unknown;
}

export async function beginManagedSession(api: string, accessKey: string, signal: AbortSignal): Promise<ManagedSession> {
  const session = parseSession(await managedJson(api, "/session", { body: { access_key: accessKey }, signal }));
  const sources = parseSources(await managedJson(api, "/sources", { token: session.token, signal }));
  return { ...session, sources };
}

export async function endManagedSession(api: string, token: string) {
  await request(api, "/session/logout", { token, body: {} });
}

export async function verifiedManagedFile(api: string, job: ManagedJob, source: ManagedSource, options: RequestOptions) {
  const response = await request(api, `/jobs/${job.id}/file`, { ...options, timeoutMs: 60000 });
  if (response.headers.get("content-length") !== String(source.size_bytes)) {
    void response.body?.cancel().catch(() => {});
    throw new Error("The download has an unexpected size.");
  }
  const bytes = await readBounded(response, source.size_bytes);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  const sha256 = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, "0")).join("");
  if (bytes.byteLength !== source.size_bytes || sha256 !== source.sha256) {
    throw new Error("The download failed integrity verification.");
  }
  return new Blob([bytes], { type: "application/octet-stream" });
}
