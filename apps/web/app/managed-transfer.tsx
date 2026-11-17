"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import {
  beginManagedSession, endManagedSession, managedApi, managedJson, ManagedRequestError, parseManagedJob,
  transferStatuses, verifiedManagedFile, type ManagedJob, type ManagedSession, type ManagedSource,
} from "./managed-transfer-api";

type Transfer = { job: ManagedJob; source: ManagedSource };
type Action = "start" | "cancel" | "download";
const expired = "Your transfer session expired. Sign in again.";

function isActive(job: ManagedJob) {
  return job.state === "queued" || job.state === "running";
}

function errorMessage(error: unknown, fallback: string) {
  return error instanceof ManagedRequestError ? error.message : fallback;
}

function TransferSession({ api, session, close }: {
  api: string;
  session: ManagedSession;
  close: (reason?: string) => void;
}) {
  const [sourceId, setSourceId] = useState("");
  const [transfer, setTransfer] = useState<Transfer | null>(null);
  const [action, setAction] = useState<Action | null>(null);
  const [notice, setNotice] = useState("");
  const operation = useRef<AbortController | null>(null);
  const active = transfer && isActive(transfer.job) ? transfer : null;
  const activeId = active?.job.id;
  const activeSource = active?.source;
  const { token, expiresAt } = session;
  const selected = session.sources.find(source => source.source_id === sourceId);

  useEffect(() => {
    const timer = setTimeout(() => close(expired), Math.max(0, expiresAt - Date.now()));
    return () => {
      clearTimeout(timer);
      operation.current?.abort();
    };
  }, [close, expiresAt]);

  useEffect(() => {
    if (!activeId || !activeSource || action === "cancel") return;
    const source = activeSource;
    const path = `/jobs/${activeId}`;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function poll() {
      try {
        const result = await managedJson(api, path, { token, signal: controller.signal });
        const job = parseManagedJob(result, source, activeId);
        if (controller.signal.aborted) return;
        setTransfer(current => current && current.job.id === activeId && isActive(current.job)
          ? { source, job } : current);
        setNotice("");
        if (isActive(job)) timer = setTimeout(poll, 1500);
      } catch (error) {
        if (controller.signal.aborted) return;
        if (error instanceof ManagedRequestError && error.status === 401) {
          close(expired);
        } else if (error instanceof ManagedRequestError && error.status === 404) {
          setTransfer(current => current?.job.id === activeId ? null : current);
          setNotice("This transfer is no longer available.");
        } else {
          setNotice("Transfer status is temporarily unavailable. Retrying.");
          timer = setTimeout(poll, 4000);
        }
      }
    }
    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [activeId, activeSource, action, api, close, token]);

  async function runAction(next: Action, run: (signal: AbortSignal) => Promise<void>, fallback: string) {
    if (operation.current) return;
    const controller = new AbortController();
    operation.current = controller;
    setAction(next);
    setNotice("");
    try {
      await run(controller.signal);
    } catch (error) {
      if (controller.signal.aborted) return;
      if (error instanceof ManagedRequestError && error.status === 401) close(expired);
      else setNotice(errorMessage(error, fallback));
    } finally {
      if (!controller.signal.aborted) setAction(null);
      operation.current = null;
    }
  }

  function start() {
    if (!selected || active) return;
    setTransfer(null);
    void runAction("start", async signal => {
      const data = await managedJson(api, "/jobs", { token, body: { source_id: selected.source_id }, signal });
      const job = parseManagedJob(data, selected);
      if (!signal.aborted) setTransfer({ job, source: selected });
    }, "Unable to start the transfer.");
  }

  function cancel() {
    if (!active) return;
    void runAction("cancel", async signal => {
      const data = await managedJson(api, `/jobs/${active.job.id}/cancel`, { token, body: {}, signal });
      const job = parseManagedJob(data, active.source, active.job.id);
      if (!signal.aborted) setTransfer({ source: active.source, job });
    }, "Unable to cancel the transfer.");
  }

  function download() {
    if (!transfer || transfer.job.state !== "completed") return;
    void runAction("download", async signal => {
      const blob = await verifiedManagedFile(api, transfer.job, transfer.source, { token, signal });
      if (signal.aborted) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = transfer.source.name;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }, "The file could not be verified. Nothing was downloaded.");
  }

  function signOut() {
    operation.current?.abort();
    // Server-side expiration also handles abandoned tabs and network failures.
    void endManagedSession(api, token).catch(() => {});
    close();
  }

  return <>
    {session.sources.length === 0 ? <p>No managed files are available.</p> : <>
      <label htmlFor="managed-source">Managed file</label>
      <select id="managed-source" value={sourceId} disabled={!!action || !!active} onChange={event => {
        setSourceId(event.target.value);
        setTransfer(null);
        setNotice("");
      }}>
        <option value="">Choose a file</option>
        {session.sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}</option>)}
      </select>
    </>}
    {transfer && <>
      <p role="status">{transferStatuses[transfer.job.state]}</p>
      {transfer.job.total_bytes > 0 &&
        <progress aria-label="Transfer progress" value={transfer.job.bytes_written} max={transfer.job.total_bytes} />}
      <p>{transfer.job.bytes_written.toLocaleString()} of {transfer.job.total_bytes.toLocaleString()} bytes</p>
    </>}
    <div className="transfer-actions">
      {session.sources.length > 0 &&
        <button className="secondary-button" disabled={!selected || !!action || !!active} onClick={start}>Start transfer</button>}
      {active &&
        <button className="secondary-button" disabled={!!action} onClick={cancel}>Cancel transfer</button>}
      {transfer?.job.state === "completed" &&
        <button className="secondary-button" disabled={!!action} onClick={download}>{action === "download" ? "Verifying…" : "Download verified file"}</button>}
      <button className="secondary-button" onClick={signOut}>Sign out</button>
    </div>
    {notice && <p className="notice" role="alert">{notice}</p>}
  </>;
}

export function ManagedTransfer({ configuredApi }: { configuredApi: string | undefined }) {
  const [api, setApi] = useState<string | null>();
  const [session, setSession] = useState<ManagedSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const signInRequest = useRef<AbortController | null>(null);

  useEffect(() => {
    const site = window.location.origin;
    setApi(window.isSecureContext && managedApi("", site) ? managedApi(configuredApi, site) : null);
    return () => signInRequest.current?.abort();
  }, [configuredApi]);

  const close = useCallback((reason = "") => {
    setSession(null);
    setNotice(reason);
  }, []);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!api || !input.current || signInRequest.current) return;
    const key = input.current.value;
    input.current.value = "";
    const controller = new AbortController();
    signInRequest.current = controller;
    setBusy(true);
    setNotice("");
    try {
      const next = await beginManagedSession(api, key, controller.signal);
      if (!controller.signal.aborted) setSession(next);
    } catch (error) {
      if (!controller.signal.aborted) {
        setNotice(error instanceof ManagedRequestError && error.status === 401
          ? "The access key was declined." : errorMessage(error, "Unable to sign in to managed downloads."));
      }
    } finally {
      if (!controller.signal.aborted) setBusy(false);
      signInRequest.current = null;
    }
  }

  return <section className="metadata managed-transfer" aria-labelledby="managed-title">
    <h2 id="managed-title">Managed downloads</h2>
    {session && api ? <TransferSession api={api} session={session} close={close} /> : api ?
      <form method="post" onSubmit={signIn}>
        <label htmlFor="managed-key">Access key</label>
        <div className="input-row">
          <input id="managed-key" ref={input} type="password" required maxLength={128} autoComplete="off" spellCheck={false} disabled={busy} />
          <button type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </div>
      </form> : api === null && <p>A secure site and a configured API origin are required.</p>}
    {notice && <p className="notice" role="alert">{notice}</p>}
  </section>;
}
