"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

let inFlightCode: string | null = null;
const exchanged = new Set<string>();

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Connecting Google…</p>}>
      <Inner />
    </Suspense>
  );
}

function Inner() {
  const params = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const error = params.get("error");
    const code = params.get("code");
    if (error) {
      router.replace(`/interviews?google=error&reason=${encodeURIComponent(error)}`);
      return;
    }
    if (!code) {
      router.replace("/interviews?google=error&reason=missing_code");
      return;
    }
    if (exchanged.has(code)) {
      router.replace("/interviews?google=connected");
      return;
    }
    if (inFlightCode === code) return;
    inFlightCode = code;
    api("/api/auth/google/exchange", {
      method: "POST",
      body: JSON.stringify({ code }),
    })
      .then(() => {
        exchanged.add(code);
        router.replace("/interviews?google=connected");
      })
      .catch((e) => {
        inFlightCode = null;
        const reason = e instanceof Error ? e.message : "exchange_failed";
        router.replace(`/interviews?google=error&reason=${encodeURIComponent(reason)}`);
      });
  }, [params, router]);

  return <p className="text-sm text-muted-foreground">Connecting Google Calendar…</p>;
}
