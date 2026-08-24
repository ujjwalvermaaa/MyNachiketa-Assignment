"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";

type Job = {
  id: number;
  title: string;
  raw_text: string;
  required_skills: string[];
  preferred_skills: string[];
  technologies: string[];
  education_requirements: string[];
  experience_requirements: string[];
  project_requirements: string[];
};

type Run = {
  id: number;
  status: string;
  total: number;
  processed: number;
  failed: number;
  current_step: string;
  current_candidate: string;
  error: string;
};

export default function ScreeningPage() {
  const [title, setTitle] = useState("GTM Engineering Intern");
  const [jd, setJd] = useState(
    "GTM Engineering Intern at myNachiketa.\n\nRequired skills: Python, FastAPI, TypeScript, Next.js, SQL, Git.\nPreferred: Gemini/LLM integration, GitHub, Google APIs, pandas.\nEducation: B.Tech or equivalent in CS or related field.\nProjects: production-quality full-stack work, AI/ML projects, research is a plus.\nExperience: internships or strong academic projects."
  );
  const [job, setJob] = useState<Job | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Job | null>("/api/jobs/latest").then((j) => {
      if (j) {
        setJob(j);
        setTitle(j.title);
        setJd(j.raw_text);
      }
    });
    api<Run | null>("/api/screening").then(setRun);
  }, []);

  useEffect(() => {
    if (!run || !["PENDING", "RUNNING"].includes(run.status)) return;
    const t = setInterval(() => {
      api<Run>(`/api/screening/${run.id}`).then(setRun);
    }, 2000);
    return () => clearInterval(t);
  }, [run?.id, run?.status]);

  async function saveJd() {
    setBusy(true);
    setError("");
    try {
      const saved = await api<Job>("/api/jobs", {
        method: "POST",
        body: JSON.stringify({ title, raw_text: jd }),
      });
      setJob(saved);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save JD");
    } finally {
      setBusy(false);
    }
  }

  async function start() {
    setBusy(true);
    setError("");
    try {
      const saved = await api<Job>("/api/jobs", {
        method: "POST",
        body: JSON.stringify({ title, raw_text: jd }),
      });
      setJob(saved);
      const started = await api<Run>("/api/screening/start", {
        method: "POST",
        body: JSON.stringify({ job_id: saved.id }),
      });
      setRun(started);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start screening");
    } finally {
      setBusy(false);
    }
  }

  const progress =
    run && run.total ? Math.round((run.processed / run.total) * 100) : 0;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Screening</p>
        <h1 className="mt-1 text-4xl">Run evaluation</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Paste the brief. Gemini extracts requirements. Then we download resumes,
          inspect repositories, and score without inventing facts.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job description</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          <Textarea
            rows={12}
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste the job description here"
          />
          <div className="flex gap-2">
            <Button onClick={saveJd} disabled={busy || !jd.trim()}>
              Save JD
            </Button>
            <Button variant="secondary" onClick={start} disabled={busy || !jd.trim()}>
              Start screening
            </Button>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {job && (
        <Card>
          <CardHeader>
            <CardTitle>Extracted requirements</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm md:grid-cols-2">
            <List label="Required skills" items={job.required_skills} />
            <List label="Preferred skills" items={job.preferred_skills} />
            <List label="Technologies" items={job.technologies} />
            <List label="Education" items={job.education_requirements} />
            <List label="Experience" items={job.experience_requirements} />
            <List label="Projects" items={job.project_requirements} />
          </CardContent>
        </Card>
      )}

      {run && (
        <Card>
          <CardHeader>
            <CardTitle>Run status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              {run.status} · {run.processed}/{run.total} · {run.failed} failed
            </p>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary" style={{ width: `${progress}%` }} />
            </div>
            {run.current_candidate && (
              <p className="text-muted-foreground">
                {run.current_step}: {run.current_candidate}
              </p>
            )}
            {run.error && <p className="text-destructive">{run.error}</p>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function List({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="font-medium">{label}</p>
      <p className="text-muted-foreground">{items.length ? items.join(", ") : "—"}</p>
    </div>
  );
}
