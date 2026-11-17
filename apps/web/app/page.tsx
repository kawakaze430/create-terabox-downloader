"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { apiErrorMessage, parseShareResolution, parseValidationResult, readApiJson, type ShareResolution, type ValidResult } from "./api-contract";
import { FixtureTransfer } from "./fixture-transfer";
import { ManagedTransfer } from "./managed-transfer";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [verified, setVerified] = useState<ValidResult | null>(null);
  const [message, setMessage] = useState("");
  const [checking, setChecking] = useState(false);
  const [resolution, setResolution] = useState<ShareResolution | null>(null);
  const validationRequest = useRef<AbortController | null>(null);
  const providerRequest = useRef<AbortController | null>(null);

  useEffect(() => {
    const incoming = new URLSearchParams(window.location.hash.slice(1)).get("url")
      ?? new URLSearchParams(window.location.search).get("url");
    if (incoming) {
      setUrl(incoming.slice(0, 2048));
      // Consume extension handoff once; do not retain private links in history.
      window.history.replaceState(null, "", window.location.pathname);
    }
    return () => { validationRequest.current?.abort(); providerRequest.current?.abort(); };
  }, []);

  async function checkLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    validationRequest.current?.abort();
    providerRequest.current?.abort();
    providerRequest.current = null;
    const controller = new AbortController();
    validationRequest.current = controller;
    const timer = window.setTimeout(() => controller.abort(), 15000);
    setChecking(false);
    setBusy(true);
    setVerified(null);
    setResolution(null);
    setMessage("");
    try {
      const response = await fetch(apiBase + "/api/v1/shares/validate", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: url.trim() }), cache: "no-store", signal: controller.signal,
      });
      const data = await readApiJson(response);
      if (!response.ok) throw new Error(apiErrorMessage(data, "Link validation failed."));
      const valid = parseValidationResult(data);
      if (validationRequest.current === controller) setVerified(valid);
    } catch (error) {
      if (validationRequest.current === controller) setMessage(controller.signal.aborted ? "The request timed out. Please try again." : error instanceof Error ? error.message : "Unexpected error. Try again.");
    } finally {
      window.clearTimeout(timer);
      if (validationRequest.current === controller) { setBusy(false); validationRequest.current = null; }
    }
  }

  async function checkProvider() {
    if (!verified) return;
    providerRequest.current?.abort();
    const controller = new AbortController();
    providerRequest.current = controller;
    const timer = window.setTimeout(() => controller.abort(), 15000);
    setChecking(true);
    setResolution(null);
    setMessage("");
    try {
      const response = await fetch(apiBase + "/api/v1/shares/resolve", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: verified.normalized_url }), cache: "no-store", signal: controller.signal,
      });
      const data = await readApiJson(response);
      if (!response.ok) throw new Error(apiErrorMessage(data, "Provider not available."));
      const metadata = parseShareResolution(data);
      if (providerRequest.current === controller) setResolution(metadata);
    } catch (error) {
      if (providerRequest.current === controller) setMessage(controller.signal.aborted ? "The request timed out. Please try again." : error instanceof Error ? error.message : "Cannot reach the service. Please try again shortly.");
    } finally {
      window.clearTimeout(timer);
      if (providerRequest.current === controller) { setChecking(false); providerRequest.current = null; }
    }
  }

  return <main className="shell">
    <header className="topbar"><div className="logo"><span className="logo-mark">↧</span> CloudLink <span className="beta">DEV PREVIEW</span></div><a href="https://github.com/sarfiaroui-oss/create-terabox-downloader" target="_blank" rel="noopener noreferrer">View source ↗</a></header>
    <section className="hero">
      <div className="eyebrow">INDEPENDENT TERABOX LINK TOOL</div>
      <h1>Understand your shared files.<br /><span>Download support is coming.</span></h1>
      <p className="intro">A trustworthy foundation for authorized TeraBox links. At this stage, you can validate a share URL. Video previews and real downloads are not connected yet.</p>
      <form onSubmit={checkLink} className="search" aria-label="Validate a share link">
        <label htmlFor="share-url">TeraBox share URL</label>
        <div className="input-row"><input id="share-url" type="url" autoComplete="off" spellCheck={false} required maxLength={2048} value={url} onChange={event => {
          validationRequest.current?.abort(); providerRequest.current?.abort();
          validationRequest.current = null; providerRequest.current = null;
          setBusy(false); setChecking(false); setVerified(null); setResolution(null); setMessage("");
          setUrl(event.target.value);
        }} placeholder="https://terabox.com/s/…" /><button type="submit" disabled={busy}>{busy ? "Checking…" : "Validate link"}</button></div>
      </form>
      {verified && <div className="result" role="status"><div className="result-title">✓ Recognized TeraBox share URL</div><p>Supported domain: <strong>{verified.hostname}</strong></p><p>{resolution ? "File metadata was returned by the API. No transfer has been performed." : "Only URL format has been validated. File access and availability have not been checked."}</p><button className="secondary-button" onClick={checkProvider} disabled={checking}>{checking ? "Checking…" : "Check downloader status"}</button></div>}
      {resolution && <section className="metadata" aria-label="Shared file metadata">
        <h2>Shared file metadata</h2>
        <p>Preview and download actions are not connected in this website.</p>
        {resolution.files.length === 0 ? <p role="status">The provider returned no files.</p> : <ul className="file-list">{resolution.files.map((file, index) => <li key={`${file.file_id}-${index}`}>
          <h3>{file.name}</h3>
          <dl><dt>Kind</dt><dd>{file.kind}</dd><dt>Size</dt><dd>{file.size_bytes === null ? "Not provided" : `${file.size_bytes.toLocaleString()} bytes`}</dd><dt>Type</dt><dd>{file.mime_type ?? "Not provided"}</dd></dl>
          {file.qualities.length > 0 && <p>Reported qualities: {file.qualities.join(", ")}</p>}
        </li>)}</ul>}
      </section>}
      {message && <p className="notice" role="alert">{message}</p>}
      {process.env.NEXT_PUBLIC_ENABLE_TRANSFER_FIXTURE === "1" && <FixtureTransfer />}
      {process.env.NEXT_PUBLIC_ENABLE_MANAGED_TRANSFERS === "1" && <ManagedTransfer configuredApi={process.env.NEXT_PUBLIC_API_BASE_URL} />}
    </section>
    <section className="features" aria-label="Development milestones"><article><span>01</span><h2>Safe link handling</h2><p>Explicit allowed domains and supported share paths, without fetching untrusted URLs.</p></article><article><span>02</span><h2>Real file metadata</h2><p>Planned next: verified filename, size, preview and supported formats.</p></article><article><span>03</span><h2>Authorized downloads</h2><p>Planned next: a tested provider adapter, permitted file access and clear errors.</p></article></section>
    <footer>This independent prototype is not affiliated with TeraBox. Use it only for files you own or are authorized to access.</footer>
  </main>;
}
