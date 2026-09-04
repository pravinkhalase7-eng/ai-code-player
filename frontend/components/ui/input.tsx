import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-14 w-full rounded-2xl border border-white/10 bg-zinc-950/60 px-5 text-base text-zinc-50 outline-none ring-amber-400/0 transition placeholder:text-zinc-500 focus:border-amber-300/40 focus:ring-4 focus:ring-amber-400/15",
        className,
      )}
      {...props}
    />
  );
}
