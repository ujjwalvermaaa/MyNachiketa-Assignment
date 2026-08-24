import { Badge } from "@/components/ui/badge";

const styles: Record<string, string> = {
  UPLOADED: "bg-stone-100 text-stone-700",
  SCREENING: "bg-indigo-50 text-indigo-700",
  SCREENED: "bg-sky-50 text-sky-800",
  SHORTLISTED: "bg-violet-50 text-violet-800",
  TEST_INVITED: "bg-amber-50 text-amber-800",
  TEST_COMPLETED: "bg-teal-50 text-teal-800",
  INTERVIEW_ELIGIBLE: "bg-emerald-50 text-emerald-800",
  INTERVIEW_SCHEDULED: "bg-indigo-100 text-indigo-900",
  FAILED: "bg-rose-50 text-rose-800",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="secondary" className={styles[status] || "bg-muted"}>
      {status.replaceAll("_", " ")}
    </Badge>
  );
}

export function score(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return Number(value).toFixed(1);
}
