"use client";

import { FormEvent, useEffect, useState } from "react";

type ValidResult = { valid: true; hostname: string; normalized_url: string };
type ApiFailure = { error?: { code: string; message: string } };
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [verified, setVerified] = useState<ValidResult | null>(null);
  const [message, setMessage] = useState("");
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    const incoming = new URLSearchParams(window.location.search).get("url");
    if (incoming) setUrl(incoming.slice(0, 2048));
  }, []);

  async function checkLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setVerified(null);
    setMessage("");
    try {
      const response = await fetch(apiBase + "/api/v1/shares/validate", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: url.trim() }), cache: "no-store",
      });
      const data = (await response.json()) as ValidResult & ApiFailure;
      if (!response.ok) throw new Error(data.error?.message ?? "Link validation failed.");
      setVerified(data);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unexpected error. Try again.");
    } finally { setBusy(false); }
  }

  async function checkProvider() {
    if (!verified) return;
    setChecking(true);
    setMessage("");
    try {
      const response = await fetch(apiBase + "/api/v1/shares/resolve", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: verified.normalized_url }), cache: "no-store",
      });
      const data = (await response.json()) as ApiFailure;
      setMessage(response.ok ? "Provider returned a response; verify the implementation before offering downloads." : data.error?.message ?? "Provider not available.");
    } catch { setMessage("Cannot reach the backend. Start the API server first."); }
    finally { setChecking(false); }
  }

  return <main className="shell">
    <header className="topbar"><div className="logo"><span className="logo-mark">↧</span> CloudLink <span className="beta">DEV PREVIEW</span></div><a href="https://github.com/kawakaze430/create-terabox-downloader" target="_blank" rel="noopener noreferrer">View source ↗</a></header>
    <section className="hero">
      <div className="eyebrow">INDEPENDENT TERABOX LINK TOOL</div>
      <h1>Understand your shared files.<br /><span>Download support is coming.</span></h1>
      <p className="intro">A trustworthy foundation for authorized TeraBox links. At this stage, you can validate a share URL. Video previews and real downloads are not connected yet.</p>
      <form onSubmit={checkLink} className="search" aria-label="Validate a share link">
        <label htmlFor="share-url">TeraBox share URL</label>
        <div className="input-row"><input id="share-url" type="url" autoComplete="url" required maxLength={2048} value={url} onChange={event => setUrl(event.target.value)} placeholder="https://terabox.com/s/…" /><button type="submit" disabled={busy}>{busy ? "Checking…" : "Validate link"}</button></div>
      </form>
      {verified && <div className="result" role="status"><div className="result-title">✓ Recognized TeraBox share URL</div><p>Supported domain: <strong>{verified.hostname}</strong></p><p>Only URL format has been validated. File access and availability have not been checked.</p><button className="secondary-button" onClick={checkProvider} disabled={checking}>{checking ? "Checking…" : "Check downloader status"}</button></div>}
      {message && <p className="notice" role="alert">{message}</p>}
    </section>
    <section className="features" aria-label="Development milestones"><article><span>01</span><h2>Safe link handling</h2><p>Explicit allowed domains and supported share paths, without fetching untrusted URLs.</p></article><article><span>02</span><h2>Real file metadata</h2><p>Planned next: verified filename, size, preview and supported formats.</p></article><article><span>03</span><h2>Authorized downloads</h2><p>Planned next: a tested provider adapter, permitted file access and clear errors.</p></article></section>
    <footer>This independent prototype is not affiliated with TeraBox. Use it only for files you own or are authorized to access.</footer>
  </main>;
}
