import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import type { PropsWithChildren } from "react";
import type { WorkspaceSection } from "../types/workspace";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

export function ContextPanelGroup({
  children,
  expanded,
  onToggle,
  section
}: PropsWithChildren<{
  expanded: boolean;
  onToggle: () => void;
  section: WorkspaceSection;
}>): JSX.Element {
  return (
    <section className="rounded-[22px] border border-slate-200/80 bg-white/95 p-3 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="text-[15px] font-semibold text-slate-900">{section.title}</h2>
            {section.status === "loading" ? <Badge variant="primary">进行中</Badge> : null}
            {section.status === "success" ? <Badge variant="success">已就绪</Badge> : null}
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-500">{section.summary}</p>
        </div>

        <Button
          aria-label={`${expanded ? "收起" : "展开"}${section.title}`}
          aria-expanded={expanded}
          className="shrink-0"
          onClick={onToggle}
          size="icon"
          type="button"
          variant="ghost"
        >
          <ChevronDown
            className={`h-4 w-4 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`.trim()}
            strokeWidth={1.8}
          />
        </Button>
      </div>

      <AnimatePresence initial={false}>
        {expanded ? (
          <motion.div
            animate={{ height: "auto", opacity: 1 }}
            className="overflow-hidden"
            exit={{ height: 0, opacity: 0 }}
            initial={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.24, ease: "easeInOut" }}
          >
            <div className="pt-3">{children}</div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}
