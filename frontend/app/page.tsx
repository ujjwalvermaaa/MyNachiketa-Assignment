"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { StatusBadge, score } from "@/components/status-badge";
import { ProfileLinks } from "@/components/profile-links";
import { api } from "@/lib/api";

type Dash = {
  totals: {
    candidates: number;
    screened: number;
    shortlisted: number;
    tests_completed: number;
    interview_eligible: number;
    interviews_scheduled: number;
  };
  top_candidates: {
    id: number;
    name: string;
    college: string;
    final_score: number | null;
    status: string;
    github_url?: string;
    resume_url?: string;
    best_ai_project?: string;
  }[];
  upcoming_interviews: {
    id: number;
    candidate_name: string;
    scheduled_at: string;
    meet_url: string;
  }[];
  latest_run: {
    id: number;
    status: string;
    processed: number;
    total: number;
    failed: number;
    current_step: string;
  } | null;
  email_safe_mode: boolean;
};

export default function DashboardPage() {
  const [data, setData] = useState<Dash | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Dash>("/api/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const hour = new Date().getHours();
  const hello = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const stats = [
    ["Candidates", data?.totals.candidates, "pipeline"],
    ["Screened", data?.totals.screened, "evaluated"],
    ["Shortlisted", data?.totals.shortlisted, "ready"],
    ["Tests done", data?.totals.tests_completed, "scored"],
    ["Interview eligible", data?.totals.interview_eligible, "next"],
    ["Scheduled", data?.totals.interviews_scheduled, "booked"],
  ] as const;

  const pulse = [
    data?.latest_run
      ? {
          title: "Screening run",
          detail: `${data.latest_run.status} · ${data.latest_run.processed}/${data.latest_run.total}`,
        }
      : { title: "Screening idle", detail: "Start a run from Screening" },
    {
      title: `${data?.totals.shortlisted ?? 0} shortlisted`,
      detail: "Ready for test invites",
    },
    {
      title: `${data?.upcoming_interviews.length ?? 0} interviews`,
      detail: "Google Meet bookings",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="size-2 rounded-full bg-[#12d4c4]" />
            Dashboard
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{hello}, recruiter</p>
          <h1 className="mt-1 max-w-xl text-4xl leading-none md:text-5xl">
            Your hiring ops{" "}
            <span className="text-primary">are running.</span>
          </h1>
        </div>
        <div className="flex gap-2">
          <Link
            href="/candidates"
            className="rounded-full border border-border bg-white px-4 py-2.5 text-sm font-medium"
          >
            + Upload CSV
          </Link>
          <Link
            href="/screening"
            className="rounded-full bg-[#111318] px-4 py-2.5 text-sm font-medium text-white"
          >
            Start screening
          </Link>
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {data?.email_safe_mode && (
        <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Email safe mode is on by design. Test and interview invitations are
          saved in the email log, not sent to real inboxes.
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
        <div className="rounded-3xl bg-[#111318] p-6 text-white shadow-sm">
          <p className="text-xs tracking-[0.2em] text-white/50 uppercase">Active pipeline</p>
          <p className="mt-3 font-[family-name:var(--font-display)] text-6xl leading-none">
            {data?.totals.candidates ?? 0}
          </p>
          <p className="mt-2 text-sm text-white/55">candidates in the desk</p>
          <div className="mt-8 grid grid-cols-3 gap-3 text-xs">
            <div>
              <p className="text-white/40">Screened</p>
              <p className="text-lg font-semibold">{data?.totals.screened ?? 0}</p>
            </div>
            <div>
              <p className="text-white/40">Shortlisted</p>
              <p className="text-lg font-semibold">{data?.totals.shortlisted ?? 0}</p>
            </div>
            <div>
              <p className="text-white/40">Interviews</p>
              <p className="text-lg font-semibold text-[#fb7185]">
                {data?.totals.interviews_scheduled ?? 0}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-3xl bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg">Live pulse</h2>
            <span className="rounded-full bg-[#e7fffb] px-2 py-1 text-[11px] font-medium text-[#0b3d38]">
              Syncing
            </span>
          </div>
          <ul className="mt-4 space-y-3">
            {pulse.map((item) => (
              <li key={item.title} className="flex gap-3 text-sm">
                <span className="mt-1 size-2 shrink-0 rounded-full bg-[#12d4c4]" />
                <span>
                  <span className="block font-medium">{item.title}</span>
                  <span className="text-xs text-muted-foreground">{item.detail}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {stats.map(([label, value]) => (
          <div key={label} className="rounded-3xl bg-white p-4 shadow-sm">
            <p className="text-[11px] tracking-[0.16em] text-muted-foreground uppercase">
              {label}
            </p>
            <p className="mt-2 font-[family-name:var(--font-display)] text-3xl">{value ?? 0}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-3xl bg-white p-5 shadow-sm">
          <h2 className="text-lg">Top candidates</h2>
          <div className="mt-4 space-y-4">
            {(data?.top_candidates || []).length === 0 && (
              <p className="text-sm text-muted-foreground">Run screening to fill this list.</p>
            )}
            {data?.top_candidates.map((c) => (
              <article key={c.id} className="rounded-2xl bg-[#f3f4f7] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <Link href={`/candidates/${c.id}`} className="font-medium hover:text-primary">
                      {c.name}
                    </Link>
                    <p className="text-xs text-muted-foreground">{c.college}</p>
                    {c.best_ai_project && (
                      <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                        {c.best_ai_project}
                      </p>
                    )}
                    <div className="mt-2">
                      <ProfileLinks githubUrl={c.github_url} resumeUrl={c.resume_url} />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-semibold">{score(c.final_score)}</p>
                    <StatusBadge status={c.status} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
        <section className="rounded-3xl bg-white p-5 shadow-sm">
          <h2 className="text-lg">Upcoming interviews</h2>
          <div className="mt-4 space-y-3">
            {(data?.upcoming_interviews || []).length === 0 && (
              <p className="text-sm text-muted-foreground">None scheduled yet.</p>
            )}
            {data?.upcoming_interviews.map((i) => (
              <div key={i.id} className="rounded-2xl bg-[#f3f4f7] px-4 py-3">
                <p className="font-medium">{i.candidate_name}</p>
                <p className="text-xs text-muted-foreground">
                  {new Date(i.scheduled_at).toLocaleString()}
                </p>
                {i.meet_url && (
                  <a href={i.meet_url} target="_blank" rel="noreferrer" className="text-xs text-primary">
                    Open Meet
                  </a>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
