"use client";

import { ReactNode, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/supabase-auth";

export default function AuthGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    getAccessToken()
      .then(token => {
        if (!active) return;
        if (!token) router.replace("/login");
        else setReady(true);
      })
      .catch(() => { if (active) router.replace("/login"); });
    return () => { active = false; };
  }, [router]);

  if (!ready) return <div className="flex min-h-[50vh] items-center justify-center text-sm text-slate-500">Checking your session…</div>;
  return <>{children}</>;
}
