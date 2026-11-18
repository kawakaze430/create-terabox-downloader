"use client";

import { useEffect, useState } from "react";
import { apiErrorMessage, readApiJson } from "./api-contract";

const fixtureSize = 262144;
const fixtureHash = "2312394bd99545d9de131c24efb781e765ac1aec243f2ed9347597a793a415e9";
const statusLabels = {
  queued: "Waiting for transfer",
  running: "Transferring fixture",
  completed: "Fixture transfer verified",
  cancelled: "Fixture transfer cancelled",
  failed: "Fixture transfer failed",
};
type State = keyof typeof statusLabels;
type Transfer = {
  id: string;
  state: State;
  bytes_written: number;
  total_bytes: number;
  sha256: string | null;
};
type Job = { transfer: Transfer; token: string };
type Action = "start" | "cancel" | "download";

function valueRecord(value: unknown): Record<string, unknown> {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) return value as Record<string, unknown>;
  throw new Error("Invalid transfer response.");
}

function opaqueId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9_-]{1,128}$/.test(value);
}

function isState(value: unknown): value is State {
  return typeof value === "string" && Object.hasOwn(statusLabels, value);
}

function parseTransfer(value: unknown, expectedId?: string): Transfer {
  const { id, state, bytes_written, total_bytes, sha256 } = valueRecord(value);
  if (!opaqueId(id) || (expectedId !== undefined && id !== expectedId) || !isState(state)
    || total_bytes !== fixtureSize || typeof bytes_written !== "number" || !Number.isInteger(bytes_written)
    || bytes_written < 0 || bytes_written > fixtureSize) throw new Error("Invalid transfer response.");
  if (state === "completed") {
    if (bytes_written !== fixtureSize || sha256 !== fixtureHash) {
      throw new Error("Invalid transfer response.");
    }
  } else if (sha256 !== null) {
    throw new Error("Invalid transfer response.");
  }
  return { id, state, bytes_written, total_bytes, sha256 };
}

function inProgress(transfer: Transfer) {
  return transfer.state === "queued" || transfer.state === "running";
}

async function fixtureFetch(api: string, path: string, token?: string, body?: unknown, signal?: AbortSignal) {
  const headers = new Headers();
  if (token) headers.set("X-Transfer-Token", token);
  if (body !== undefined) headers.set("Content-Type", "application/json");
  const timeout = AbortSignal.timeout(5000);
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
    const error = await response.json().catch(() => null);
    throw new Error(apiErrorMessage(error, "The local transfer service could not complete the request."));
  }
  return response;
}

export function FixtureTransfer() {
  const [api, setApi] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [action, setAction] = useState<Action | null>(null);
  const [notice, setNotice] = useState("");
  const activeJob = job && inProgress(job.transfer) ? job : null;
  const activeId = activeJob?.transfer.id;
  const activeToken = activeJob?.token;

  useEffect(() => {
    const { protocol, hostname } = window.location;
    if (protocol === "http:" && ["127.0.0.1", "localhost", "[::1]"].includes(hostname)) {
      setApi(`http://${hostname}:8000/api/v1/fixture-transfers`);
    }
  }, []);

  useEffect(() => {
    if (!api || !activeId || !activeToken || action === "cancel") return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const path = `/jobs/${activeId}`;
    async function poll() {
      try {
        const response = await fixtureFetch(api, path, activeToken, undefined, controller.signal);
        const transfer = parseTransfer(await readApiJson(response), activeId);
        if (controller.signal.aborted) return;
        setJob(current => current && current.transfer.id === activeId && inProgress(current.transfer)
          ? { ...current, transfer }
          : current);
        if (inProgress(transfer)) timer = setTimeout(poll, 250);
      } catch {
        if (!controller.signal.aborted) {
          setJob(current => current?.transfer.id === activeId ? null : current);
          setNotice("Transfer status is unavailable. Start a new test transfer.");
        }
      }
    }
    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [api, activeId, activeToken, action]);

  if (!api) return null;

  async function start() {
    setAction("start");
    setJob(null);
    setNotice("");
    try {
      const source = valueRecord(await readApiJson(await fixtureFetch(api, "/source")));
      if (!opaqueId(source.source_id)) throw new Error("Invalid fixture source response.");
      const created = valueRecord(await readApiJson(await fixtureFetch(api, "/jobs", undefined, { source_id: source.source_id })));
      if (!opaqueId(created.token)) throw new Error("Invalid transfer response.");
      setJob({ transfer: parseTransfer(created), token: created.token });
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to start the fixture transfer.");
    } finally {
      setAction(null);
    }
  }

  async function cancel() {
    if (!activeJob) return;
    setAction("cancel");
    setNotice("");
    const { id } = activeJob.transfer;
    try {
      const response = await fixtureFetch(api, `/jobs/${id}/cancel`, activeJob.token, {});
      setJob({ ...activeJob, transfer: parseTransfer(await readApiJson(response), id) });
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to cancel the fixture transfer.");
    } finally {
      setAction(null);
    }
  }

  async function download() {
    if (!job || job.transfer.state !== "completed") return;
    setAction("download");
    setNotice("");
    try {
      const response = await fixtureFetch(api, `/jobs/${job.transfer.id}/file`, job.token);
      if (response.headers.get("content-length") !== String(job.transfer.total_bytes)) {
        throw new Error("The downloaded fixture has an unexpected size.");
      }
      const bytes = await response.arrayBuffer();
      const hash = await crypto.subtle.digest("SHA-256", bytes);
      const sha256 = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, "0")).join("");
      if (bytes.byteLength !== job.transfer.total_bytes || sha256 !== job.transfer.sha256) {
        throw new Error("The downloaded fixture failed integrity verification.");
      }
      const url = URL.createObjectURL(new Blob([bytes], { type: "application/octet-stream" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "transfer-fixture.bin";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to download the verified fixture.");
    } finally {
      setAction(null);
    }
  }

  return <section className="metadata fixture-transfer" aria-labelledby="fixture-title">
    <h2 id="fixture-title">Local test transfer</h2>
    <p>Send a 256 KiB test file through the local download engine.</p>
    {job && <>
      <p role="status">{statusLabels[job.transfer.state]}</p>
      <progress aria-label="Fixture transfer progress" value={job.transfer.bytes_written} max={job.transfer.total_bytes} />
      <p>{job.transfer.bytes_written.toLocaleString()} of {job.transfer.total_bytes.toLocaleString()} bytes</p>
    </>}
    <div className="transfer-actions">
      <button className="secondary-button" disabled={!!action || !!activeJob} onClick={start}>{action === "start" ? "Starting…" : "Start test transfer"}</button>
      {activeJob && <button className="secondary-button" disabled={!!action} onClick={cancel}>{action === "cancel" ? "Cancelling…" : "Cancel transfer"}</button>}
      {job?.transfer.state === "completed" && <button className="secondary-button" disabled={!!action} onClick={download}>{action === "download" ? "Verifying…" : "Download verified fixture"}</button>}
    </div>
    {notice && <p className="notice" role="alert">{notice}</p>}
  </section>;
}
