"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Dashboard", icon: IconGrid },
  { href: "/candidates", label: "Candidates", icon: IconUsers },
  { href: "/screening", label: "Screening", icon: IconSpark },
  { href: "/ranking", label: "Ranking", icon: IconRank },
  { href: "/tests", label: "Tests", icon: IconClip },
  { href: "/interviews", label: "Interviews", icon: IconCal },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-screen bg-[#f3f4f7]">
      <aside className="sticky top-0 flex h-screen w-[88px] flex-col items-center bg-[#141416] py-5 lg:w-64 lg:items-stretch lg:px-4">
        <Link href="/" className="mb-8 flex items-center gap-3 px-1">
          <span className="grid size-10 place-items-center rounded-2xl bg-[#12d4c4] text-sm font-bold text-[#06221f]">
            MN
          </span>
          <span className="hidden lg:block">
            <span className="block text-sm font-semibold text-white">myNachiketa</span>
            <span className="text-[11px] text-white/45">Command center</span>
          </span>
        </Link>
        <nav className="flex flex-1 flex-col gap-1">
          {links.map((link) => {
            const active =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex items-center justify-center gap-3 rounded-2xl px-3 py-2.5 text-sm lg:justify-start",
                  active
                    ? "bg-[#12d4c4] font-semibold text-[#06221f]"
                    : "text-white/55 hover:bg-white/5 hover:text-white"
                )}
              >
                <Icon />
                <span className="hidden lg:inline">{link.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="hidden rounded-2xl bg-white/5 p-3 lg:block">
          <p className="text-xs font-medium text-white">Recruiter</p>
          <p className="truncate text-[11px] text-white/40">myNachiketa screening</p>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between gap-4 px-6 py-4">
          <div className="flex max-w-xl flex-1 items-center gap-2 rounded-full bg-white px-4 py-2.5 text-sm text-muted-foreground shadow-sm">
            <span>Search candidates, ranks, interviews…</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-right text-sm sm:block">
              <span className="block font-medium">Recruiter</span>
              <span className="text-xs text-muted-foreground">Admin</span>
            </span>
            <span className="grid size-10 place-items-center rounded-full bg-[#111318] text-xs font-semibold text-white">
              RN
            </span>
          </div>
        </header>
        <main className="dash-texture px-6 pb-10">{children}</main>
      </div>
    </div>
  );
}

function IconGrid() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="3" width="7" height="7" rx="1.6" />
      <rect x="14" y="3" width="7" height="7" rx="1.6" />
      <rect x="3" y="14" width="7" height="7" rx="1.6" />
      <rect x="14" y="14" width="7" height="7" rx="1.6" />
    </svg>
  );
}
function IconUsers() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 19c.6-3 2.8-5 5.5-5s4.9 2 5.5 5" />
      <circle cx="17" cy="9" r="2.2" />
      <path d="M16 19c.4-2 1.7-3.4 3.6-4" />
    </svg>
  );
}
function IconSpark() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3l1.6 5.2L19 10l-5.4 1.8L12 17l-1.6-5.2L5 10l5.4-1.8L12 3z" />
    </svg>
  );
}
function IconRank() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 19V11M12 19V5M20 19v-7" />
    </svg>
  );
}
function IconClip() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="6" y="4" width="12" height="16" rx="2" />
      <path d="M9 9h6M9 13h6" />
    </svg>
  );
}
function IconCal() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="4" y="5" width="16" height="15" rx="2" />
      <path d="M4 10h16M8 3v4M16 3v4" />
    </svg>
  );
}
