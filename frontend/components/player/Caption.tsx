"use client";

export function Caption({ text }: { text: string }) {
  if (!text) return null;
  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-4 mx-auto max-w-3xl px-4">
      <p className="rounded-2xl bg-black/70 px-4 py-2 text-center text-sm text-white shadow-lg">
        {text}
      </p>
    </div>
  );
}
