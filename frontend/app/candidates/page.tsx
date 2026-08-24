"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/status-badge";
import { ProfileLinks, clip } from "@/components/profile-links";
import { api, upload } from "@/lib/api";
import type { Candidate } from "@/lib/types";

type UploadResult = {
  imported: number;
  duplicates: string[];
  duplicate_emails?: string[];
  validation_errors: { row: number; error: string }[];
  preview: { name: string; email: string; college: string }[];
};

export default function CandidatesPage() {
  const [rows, setRows] = useState<Candidate[]>([]);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = () =>
    api<Candidate[]>("/api/candidates").then(setRows).catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  async function onFile(file?: File) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      setResult(await upload<UploadResult>("/api/candidates/upload", file));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm text-muted-foreground">Candidates</p>
        <h1 className="mt-1 text-4xl">Candidate list</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Every person in the room: college, research, best AI project, GitHub, and resume.
          Upload CSV or the supplied XLSX.
        </p>
      </div>

      <div className="rounded-3xl border border-border bg-card p-5">
        <p className="text-sm font-medium">Bring in a list</p>
        <Input
          className="mt-3"
          type="file"
          accept=".csv,.xlsx,.xls"
          disabled={busy}
          onChange={(e) => onFile(e.target.files?.[0])}
        />
        {busy && <p className="mt-2 text-sm text-muted-foreground">Importing…</p>}
        {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        {result && (
          <div className="mt-3 space-y-1 text-sm">
            <p>
              Imported <strong>{result.imported}</strong>
            </p>
            {result.duplicate_emails && result.duplicate_emails.length > 0 && (
              <p className="text-primary">
                Shared demo emails kept: {result.duplicate_emails.join(", ")}
              </p>
            )}
          </div>
        )}
      </div>

      <div className="grid gap-4">
        {rows.map((c, i) => (
          <article key={c.id} className="rounded-3xl border border-border bg-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-[11px] tracking-[0.24em] text-primary">
                  {String(i + 1).padStart(2, "0")}
                </p>
                <Link href={`/candidates/${c.id}`} className="text-2xl hover:text-primary">
                  {c.name}
                </Link>
                <p className="text-sm text-muted-foreground">
                  {c.college} · {c.branch} · CGPA {c.cgpa ?? "—"}
                </p>
                <p className="text-xs text-muted-foreground">{c.email}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <StatusBadge status={c.status} />
                <ProfileLinks
                  githubUrl={c.github_url}
                  githubUsername={c.github_username}
                  resumeUrl={c.resume_url}
                />
              </div>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-[11px] tracking-widest text-muted-foreground uppercase">
                  Best AI project
                </p>
                <p className="mt-1 text-sm leading-relaxed">{clip(c.best_ai_project, 280)}</p>
              </div>
              <div>
                <p className="text-[11px] tracking-widest text-muted-foreground uppercase">
                  Research
                </p>
                <p className="mt-1 text-sm leading-relaxed">{clip(c.research_work, 280)}</p>
              </div>
            </div>
          </article>
        ))}
        {rows.length === 0 && (
          <p className="py-10 text-center text-sm text-muted-foreground">No dossiers yet.</p>
        )}
      </div>
    </div>
  );
}
