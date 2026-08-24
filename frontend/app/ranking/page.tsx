"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { StatusBadge, score } from "@/components/status-badge";
import { ProfileLinks, clip } from "@/components/profile-links";
import { api } from "@/lib/api";
import type { RankRow } from "@/lib/types";

type SortKey = keyof RankRow;

export default function RankingPage() {
  const [rows, setRows] = useState<RankRow[]>([]);
  const [sort, setSort] = useState<SortKey>("rank");
  const [dir, setDir] = useState<"asc" | "desc">("asc");
  const [selected, setSelected] = useState<number[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api<RankRow[]>("/api/rankings").then(setRows).catch((e) => setError(e.message));
  }, []);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sort];
      const bv = b[sort];
      if (av === bv) return 0;
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      const cmp = av < bv ? -1 : 1;
      return dir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [rows, sort, dir]);

  function toggle(key: SortKey) {
    if (sort === key) setDir(dir === "asc" ? "desc" : "asc");
    else {
      setSort(key);
      setDir(key === "rank" || key === "name" ? "asc" : "desc");
    }
  }

  async function invite() {
    try {
      const data = await api<{ results: { email: string; status: string }[] }>(
        "/api/tests/invite",
        { method: "POST", body: JSON.stringify({ candidate_ids: selected }) }
      );
      setMessage(`Invited ${data.results.length} candidate(s).`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invite failed");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Ranking</p>
          <h1 className="mt-1 text-4xl">Ranked candidates</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Ranked by Python weights on Gemini component scores. Top three are
            marked. Open a name for the full explainable write-up.
          </p>
        </div>
        <Button disabled={!selected.length} onClick={invite}>
          Send trial invite
        </Button>
      </div>
      {message && <p className="text-sm text-emerald-800">{message}</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="space-y-4">
        {sorted.map((row) => (
          <article
            key={row.id}
            className={`rounded-3xl border bg-card p-5 shadow-sm ${
              row.rank && row.rank <= 3 ? "border-primary" : "border-border"
            }`}
          >
            <div className="flex flex-wrap items-start gap-4">
              <label className="mt-2">
                <input
                  type="checkbox"
                  checked={selected.includes(row.id)}
                  onChange={(e) =>
                    setSelected(
                      e.target.checked
                        ? [...selected, row.id]
                        : selected.filter((id) => id !== row.id)
                    )
                  }
                />
              </label>
              <div className="min-w-14">
                <p className="font-[family-name:var(--font-display)] text-3xl">
                  {row.rank ? String(row.rank).padStart(2, "0") : "—"}
                </p>
                {row.rank && row.rank <= 3 && (
                  <p className="text-[10px] tracking-widest text-primary uppercase">
                    Lead
                  </p>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <Link href={`/candidates/${row.id}`} className="text-2xl hover:text-primary">
                      {row.name}
                    </Link>
                    <p className="text-sm text-muted-foreground">
                      {row.college} · {row.branch} · CGPA {row.cgpa ?? "—"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-[family-name:var(--font-display)] text-3xl">
                      {score(row.final_score)}
                    </p>
                    <StatusBadge status={row.status} />
                  </div>
                </div>
                <div className="mt-3">
                  <ProfileLinks
                    githubUrl={row.github_url}
                    githubUsername={row.github_username}
                    resumeUrl={row.resume_url}
                  />
                </div>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <p className="text-sm">
                    <span className="text-[11px] tracking-widest text-muted-foreground uppercase">
                      Best AI project
                    </span>
                    <span className="mt-1 block">{clip(row.best_ai_project, 220)}</span>
                  </p>
                  <p className="text-sm">
                    <span className="text-[11px] tracking-widest text-muted-foreground uppercase">
                      Research
                    </span>
                    <span className="mt-1 block">{clip(row.research_work, 220)}</span>
                  </p>
                </div>
                <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
                  <button type="button" onClick={() => toggle("resume_score")}>
                    Resume {score(row.resume_score)}
                  </button>
                  <button type="button" onClick={() => toggle("ai_project_score")}>
                    AI {score(row.ai_project_score)}
                  </button>
                  <button type="button" onClick={() => toggle("github_score")}>
                    GitHub {score(row.github_score)}
                  </button>
                  <button type="button" onClick={() => toggle("research_score")}>
                    Research {score(row.research_score)}
                  </button>
                  <button type="button" onClick={() => toggle("pre_test_score")}>
                    Pre-test {score(row.pre_test_score)}
                  </button>
                  <button type="button" onClick={() => toggle("test_score")}>
                    Trial {score(row.test_score)}
                  </button>
                </div>
              </div>
            </div>
          </article>
        ))}
        {sorted.length === 0 && (
          <p className="text-sm text-muted-foreground">Upload candidates first.</p>
        )}
      </div>
    </div>
  );
}
