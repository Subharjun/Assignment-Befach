export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-black/10 dark:border-white/10 overflow-hidden">
      <div className="aspect-square shimmer animate-shimmer" />
      <div className="p-3 space-y-2">
        <div className="h-3 w-1/3 shimmer animate-shimmer rounded" />
        <div className="h-4 w-5/6 shimmer animate-shimmer rounded" />
        <div className="h-4 w-1/3 shimmer animate-shimmer rounded" />
      </div>
    </div>
  );
}

export function GridSkeleton({ n = 8 }: { n?: number }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: n }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}
