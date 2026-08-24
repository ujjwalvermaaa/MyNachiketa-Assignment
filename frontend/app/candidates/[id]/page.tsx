"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { StatusBadge, score } from "@/components/status-badge";
import { ProfileLinks, githubHref } from "@/components/profile-links";
import { api } from "@/lib/api";
import type { Candidate } from "@/lib/types";

type Detail = Candidate & {
  resume_text: string;
  evaluation: {
    matching_skills: string[];
    strengths: string[];
    gaps: string[];
    evidence: string[];
    github_evidence: string[];
    reasoning: string;
  } | null;
  github_repos: {
    full_name: string;
    description: string;
    language: string;
    is_relevant: boolean;
    relevance_notes: string;
    readme_excerpt: string;
  }[];
};

export default function CandidateDetailPage() {
  const params = useParams<{ id: string }>();
  const [c, setC] = useState<Detail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Detail>(`/api/candidates/${params.id}`)
      .then(setC)
      .catch((e) => setError(e.message));
  }, [params.id]);

  if (error) return <p className="text-destructive">{error}</p>;
  if (!c) return <p className="text-sm text-muted-foreground">Opening dossier…</p>;

  const evaln = c.evaluation;
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Explainable scoring</p>
          <h1 className="mt-1 text-4xl">{c.name}</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {c.college} · {c.branch} · CGPA {c.cgpa ?? "—"}
          </p>
          <p className="text-xs text-muted-foreground">{c.email}</p>
          <div className="mt-3">
            <StatusBadge status={c.status} />
          </div>
        </div>
        <ProfileLinks
          githubUrl={c.github_url}
          githubUsername={c.github_username}
          resumeUrl={c.resume_url}
        />
      </div>

      {c.processing_error && (
        <p className="border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {c.processing_error}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          ["Resume", c.resume_score],
          ["AI project", c.ai_project_score],
          ["GitHub", c.github_score],
          ["Research", c.research_score],
          ["CGPA", c.cgpa_score],
          ["Pre-test", c.pre_test_score],
          ["Trial", c.test_score],
          ["Final", c.final_score],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-3xl border border-border bg-card p-4">
            <p className="text-[11px] tracking-widest text-muted-foreground uppercase">
              {label}
            </p>
            <p className="mt-1 font-[family-name:var(--font-display)] text-3xl">
              {score(value as number | null)}
            </p>
          </div>
        ))}
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-3xl border border-border bg-card p-5">
          <h2 className="text-2xl">Best AI project</h2>
          <p className="mt-3 text-sm leading-relaxed whitespace-pre-wrap">
            {c.best_ai_project || "Not provided in the dataset."}
          </p>
        </div>
        <div className="rounded-3xl border border-border bg-card p-5">
          <h2 className="text-2xl">Research</h2>
          <p className="mt-3 text-sm leading-relaxed whitespace-pre-wrap">
            {c.research_work || "Not provided in the dataset."}
          </p>
        </div>
      </section>

      <section className="rounded-3xl border border-border bg-card p-5">
        <h2 className="text-2xl">Why this score</h2>
        <p className="mt-3 text-sm leading-relaxed">
          {evaln?.reasoning || "Run the atelier so Gemini can ground this write-up in resume and repository evidence."}
        </p>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Section title="Matching skills" items={evaln?.matching_skills} />
          <Section title="Resume evidence" items={evaln?.evidence} />
          <Section title="GitHub evidence" items={evaln?.github_evidence} />
          <Section title="Strengths" items={evaln?.strengths} />
          <Section title="Gaps" items={evaln?.gaps} />
        </div>
      </section>

      <section className="rounded-3xl border border-border bg-card p-5">
        <h2 className="text-2xl">Repositories inspected</h2>
        <div className="mt-4 space-y-3">
          {c.github_repos.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No repositories stored yet. Missing GitHub is scored as a gap, not a crash.
            </p>
          )}
          {c.github_repos.map((repo) => (
            <a
              key={repo.full_name}
              href={`https://github.com/${repo.full_name}`}
              target="_blank"
              rel="noreferrer"
              className="block border border-border p-4 hover:border-primary"
            >
              <p className="font-medium">
                {repo.full_name}{" "}
                <span className="text-xs text-muted-foreground">{repo.language}</span>
              </p>
              <p className="text-sm text-muted-foreground">{repo.description}</p>
              <p className="mt-1 text-xs">{repo.relevance_notes}</p>
            </a>
          ))}
        </div>
        {githubHref(c.github_url, c.github_username) && (
          <a
            className="mt-4 inline-block text-sm text-primary"
            href={githubHref(c.github_url, c.github_username)}
            target="_blank"
            rel="noreferrer"
          >
            Open full GitHub profile →
          </a>
        )}
      </section>
    </div>
  );
}

function Section({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="text-[11px] tracking-widest text-muted-foreground uppercase">{title}</p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
