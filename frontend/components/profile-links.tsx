export function githubHref(url?: string, username?: string) {
  if (url && /^https?:\/\//i.test(url)) return url;
  if (username) return `https://github.com/${username}`;
  return "";
}

export function ProfileLinks({
  githubUrl,
  githubUsername,
  resumeUrl,
}: {
  githubUrl?: string;
  githubUsername?: string;
  resumeUrl?: string;
}) {
  const git = githubHref(githubUrl, githubUsername);
  if (!git && !resumeUrl) {
    return <span className="text-xs text-muted-foreground">No profile links</span>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {git && (
        <a
          href={git}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="inline-flex items-center rounded-full bg-[#e7fffb] px-2.5 py-1 text-[11px] font-medium text-[#0b3d38]"
        >
          GitHub ↗
        </a>
      )}
      {resumeUrl && (
        <a
          href={resumeUrl}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="inline-flex items-center rounded-full bg-[#111318] px-2.5 py-1 text-[11px] font-medium text-white"
        >
          Resume ↗
        </a>
      )}
    </div>
  );
}

export function clip(text?: string, n = 160) {
  if (!text) return "Not provided";
  return text.length > n ? `${text.slice(0, n).trim()}…` : text;
}
