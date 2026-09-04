"use client";

import { motion } from "framer-motion";
import type { VariableSnapshot } from "@/types/lesson";

export function VariablePanel({ variables }: { variables: VariableSnapshot[] }) {
  return (
    <div className="rounded-2xl border border-amber-300/20 bg-amber-400/5 p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
        Variables
      </p>
      {variables.length === 0 ? (
        <p className="text-sm text-zinc-400">Waiting for the first assignment.</p>
      ) : (
        variables.map((item) => (
          <div key={item.name} className="flex items-center justify-between text-sm">
            <span className="font-mono text-zinc-300">{item.name}</span>
            <motion.span
              key={item.value}
              initial={{ scale: 0.7, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="rounded-lg bg-zinc-950 px-3 py-1 font-mono text-amber-200"
            >
              {item.value}
            </motion.span>
          </div>
        ))
      )}
    </div>
  );
}
