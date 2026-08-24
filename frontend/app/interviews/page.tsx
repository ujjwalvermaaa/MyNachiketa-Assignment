"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Candidate } from "@/lib/types";

type Interview = {
  id: number;
  candidate_name: string;
  candidate_email: string;
  scheduled_at: string;
  duration_minutes: number;
  meet_url: string;
  event_url: string;
  status: string;
  email_sent: boolean;
};

export default function InterviewsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Loading interviews…</p>}>
      <InterviewsInner />
    </Suspense>
  );
}

function InterviewsInner() {
  const params = useSearchParams();
  const [connected, setConnected] = useState(false);
  const [redirectUri, setRedirectUri] = useState("http://localhost:3000/auth/callback");
  const [origin, setOrigin] = useState("http://localhost:3000");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [candidateId, setCandidateId] = useState("");
  const [when, setWhen] = useState("");
  const [duration, setDuration] = useState(30);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState("");

  async function load() {
    const status = await api<{
      connected: boolean;
      redirect_uri?: string;
      javascript_origin?: string;
    }>("/api/calendar/status");
    setConnected(status.connected);
    if (status.redirect_uri) setRedirectUri(status.redirect_uri);
    if (status.javascript_origin) setOrigin(status.javascript_origin);
    setCandidates(await api<Candidate[]>("/api/candidates"));
    setInterviews(await api<Interview[]>("/api/interviews"));
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (params.get("google") === "connected") {
      setMessage("Google Calendar is connected.");
      setError("");
    }
    if (params.get("google") === "error") {
      const reason = params.get("reason") || "";
      setError(
        reason
          ? `Google login did not finish: ${reason}. Click Connect Google Calendar again.`
          : "Google login did not finish. Click Connect Google Calendar again."
      );
    }
  }, [params]);

  async function connect() {
    const data = await api<{ url: string }>("/api/auth/google/login");
    window.location.href = data.url;
  }

  async function schedule() {
    setBusy(true);
    setError("");
    try {
      await api("/api/interviews/schedule", {
        method: "POST",
        body: JSON.stringify({
          candidate_id: Number(candidateId),
          scheduled_at: new Date(when).toISOString(),
          duration_minutes: duration,
        }),
      });
      setMessage("Interview booked with a Google Meet link.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not schedule");
    } finally {
      setBusy(false);
    }
  }

  function copy(label: string, value: string) {
    navigator.clipboard.writeText(value);
    setCopied(label);
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Interviews</p>
        <h1 className="mt-1 text-4xl">Schedule with Meet</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Connect Google Calendar once, then book a candidate. Meet is created by Google Calendar,
          not faked. If email fails, the interview stays booked.
        </p>
      </div>

      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl">Google Calendar</h2>
            <p className="text-sm text-muted-foreground">
              {connected
                ? "Connected — you can book interviews below."
                : "Not connected yet. Google must finish handing tokens back to this app."}
            </p>
          </div>
          <Button onClick={connect}>{connected ? "Reconnect Google Calendar" : "Connect Google Calendar"}</Button>
        </div>
        {!connected && (
        <div className="mt-5 space-y-3 rounded-2xl bg-[#f3f4f7] p-4 text-sm">
          <p className="font-medium">Do this once in Google Cloud (Web application client):</p>
          <ol className="list-decimal space-y-1 pl-5 text-muted-foreground">
            <li>
              Open{" "}
              <a
                className="text-primary underline"
                href="https://console.cloud.google.com/apis/credentials"
                target="_blank"
                rel="noreferrer"
              >
                Google Cloud credentials
              </a>
            </li>
            <li>Click the OAuth client that matches this app (Web application)</li>
            <li>Add the JavaScript origin and redirect URI below, then Save</li>
            <li>Wait 1–2 minutes, then connect again</li>
          </ol>
          <CopyRow label="JavaScript origin" value={origin} copied={copied} onCopy={copy} />
          <CopyRow label="Redirect URI" value={redirectUri} copied={copied} onCopy={copy} />
          <p className="text-xs text-muted-foreground">
            Google shows <code>ujjwalvermauv2004@gmail.com</code> because that is the Google account
            currently signed in on Chrome. Sign in with the account that owns the OAuth client if
            needed. The mismatch error is only about the URI list, not that email.
          </p>
        </div>
        )}
      </section>

      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <h2 className="text-xl">Book an interview</h2>
        <div className="mt-4 grid gap-3">
          <select
            className="h-11 rounded-2xl border border-border bg-white px-3 text-sm"
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
          >
            <option value="">Select candidate</option>
            {candidates.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.status})
              </option>
            ))}
          </select>
          <Input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
          <Input
            type="number"
            min={15}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
          <Button disabled={busy || !connected || !candidateId || !when} onClick={schedule}>
            Schedule interview
          </Button>
          {message && <p className="text-sm text-emerald-700">{message}</p>}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
      </section>

      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <h2 className="text-xl">Scheduled</h2>
        <div className="mt-4 space-y-3">
          {interviews.map((i) => (
            <div key={i.id} className="rounded-2xl bg-[#f3f4f7] p-4 text-sm">
              <p className="font-medium">{i.candidate_name}</p>
              <p className="text-muted-foreground">
                {new Date(i.scheduled_at).toLocaleString()} · {i.duration_minutes} min
              </p>
              {i.meet_url && (
                <a className="text-primary" href={i.meet_url} target="_blank" rel="noreferrer">
                  Google Meet
                </a>
              )}
              {!i.email_sent && (
                <Button
                  className="mt-2"
                  size="sm"
                  onClick={() =>
                    api(`/api/interviews/${i.id}/send-invitation`, { method: "POST" }).then(load)
                  }
                >
                  Retry invitation
                </Button>
              )}
            </div>
          ))}
          {interviews.length === 0 && (
            <p className="text-sm text-muted-foreground">No interviews yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function CopyRow({
  label,
  value,
  copied,
  onCopy,
}: {
  label: string;
  value: string;
  copied: string;
  onCopy: (label: string, value: string) => void;
}) {
  return (
    <div>
      <p className="text-[11px] tracking-widest text-muted-foreground uppercase">{label}</p>
      <div className="mt-1 flex gap-2">
        <code className="flex-1 rounded-xl bg-white px-3 py-2 text-xs">{value}</code>
        <Button type="button" variant="outline" onClick={() => onCopy(label, value)}>
          {copied === label ? "Copied" : "Copy"}
        </Button>
      </div>
    </div>
  );
}
