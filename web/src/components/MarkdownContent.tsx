import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "../lib/cn";

export function MarkdownContent({
  content,
  className,
}: {
  content: string;
  className?: string;
}): JSX.Element {
  return (
    <div className={cn("markdown-content min-w-0 text-[14px] leading-7 text-slate-700", className)}>
      <ReactMarkdown
        components={{
          h1: ({ children }) => (
            <h1 className="mt-4 text-xl font-semibold tracking-tight text-slate-950 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mt-4 text-lg font-semibold tracking-tight text-slate-950 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-4 text-base font-semibold tracking-tight text-slate-900 first:mt-0">
              {children}
            </h3>
          ),
          p: ({ children }) => <p className="mt-3 first:mt-0">{children}</p>,
          ul: ({ children }) => <ul className="mt-3 list-disc space-y-1 pl-5 first:mt-0">{children}</ul>,
          ol: ({ children }) => <ol className="mt-3 list-decimal space-y-1 pl-5 first:mt-0">{children}</ol>,
          li: ({ children }) => <li>{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="mt-4 border-l-2 border-slate-300 pl-4 text-slate-600 first:mt-0">
              {children}
            </blockquote>
          ),
          a: ({ children, href }) => (
            <a
              className="font-medium text-sky-700 underline decoration-sky-300 underline-offset-4 transition hover:text-sky-800"
              href={href}
              rel="noreferrer"
              target="_blank"
            >
              {children}
            </a>
          ),
          pre: ({ children }) => (
            <pre className="scrollbar-subtle mt-4 overflow-x-auto rounded-2xl bg-slate-900 px-4 py-3 text-[13px] leading-6 text-slate-100 first:mt-0">
              {children}
            </pre>
          ),
          code: ({ children, className: codeClassName }) => {
            const isBlock = typeof codeClassName === "string" && codeClassName.length > 0;
            if (isBlock) {
              return <code className={codeClassName}>{children}</code>;
            }

            return (
              <code className="rounded-md bg-slate-100 px-1.5 py-0.5 font-mono text-[13px] text-slate-800">
                {children}
              </code>
            );
          },
          table: ({ children }) => (
            <div className="scrollbar-subtle mt-4 overflow-x-auto first:mt-0">
              <table className="min-w-full border-collapse overflow-hidden rounded-2xl border border-slate-200 bg-white text-left text-[13px] leading-6">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-slate-50 text-slate-500">{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => <tr className="border-t border-slate-200">{children}</tr>,
          th: ({ children }) => <th className="px-3 py-2 font-semibold text-slate-700">{children}</th>,
          td: ({ children }) => <td className="px-3 py-2 align-top text-slate-600">{children}</td>,
        }}
        remarkPlugins={[remarkGfm]}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
