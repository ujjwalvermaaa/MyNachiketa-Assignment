"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api, upload } from "@/lib/api";
import { score } from "@/components/status-badge";

type TestRow = {
  id: number;
  email: string;
  candidate_id: number | null;
  logical_score: number | null;
  coding_score: number | null;
  computed_test_score: number | null;
  matched: boolean;
};

type UploadResult = {
  matched: { email: string; name: string; test_score: number; final_score: number }[];
  unmatched: { email: string }[];
  validation_errors: { row: number; error: string }[];
};

export default function TestsPage() {
  const [rows, setRows] = useState<TestRow[]>([]);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => api<TestRow[]>("/api/tests").then(setRows);

  useEffect(() => {
    load();
  }, []);

  async function onFile(file?: File) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      setResult(await upload<UploadResult>("/api/tests/upload", file));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function inviteAll() {
    setBusy(true);
    try {
      await api("/api/tests/invite", {
        method: "POST",
        body: JSON.stringify({ send_all_shortlisted: true }),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invite failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Tests</p>
        <h1 className="mt-1 text-4xl">Test invites & results</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Send test invites, then upload logical + coding scores. Matching is by
          email, with name as fallback for the demo dataset.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button onClick={inviteAll} disabled={busy}>
            Send tests to shortlisted
          </Button>
          <Input
            type="file"
            accept=".csv,.xlsx,.xls"
            disabled={busy}
            onChange={(e) => onFile(e.target.files?.[0])}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          {result && (
            <div className="text-sm">
              <p>Matched: {result.matched.length}</p>
              {result.unmatched.length > 0 && (
                <p className="text-amber-800">
                  Unmatched emails: {result.unmatched.map((u) => u.email).join(", ")}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Logical</TableHead>
                <TableHead>Coding</TableHead>
                <TableHead>Test score</TableHead>
                <TableHead>Matched</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.id} className={!r.matched ? "bg-amber-50" : undefined}>
                  <TableCell>{r.email}</TableCell>
                  <TableCell>{score(r.logical_score)}</TableCell>
                  <TableCell>{score(r.coding_score)}</TableCell>
                  <TableCell>{score(r.computed_test_score)}</TableCell>
                  <TableCell>{r.matched ? "Yes" : "No"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
