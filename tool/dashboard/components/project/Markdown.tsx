"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Hiển thị Markdown (kịch bản, lời thoại) với kiểu chữ gọn, có bảng/checkbox (GFM). */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="text-[13px] leading-relaxed text-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (p) => <h1 className="mb-3 mt-1 text-lg font-semibold tracking-tight" {...p} />,
          h2: (p) => <h2 className="mb-2 mt-5 border-b border-border pb-1 text-[15px] font-semibold" {...p} />,
          h3: (p) => <h3 className="mb-1.5 mt-4 text-sm font-semibold" {...p} />,
          h4: (p) => <h4 className="mb-1 mt-3 text-[13px] font-semibold text-muted-foreground" {...p} />,
          p: (p) => <p className="my-2" {...p} />,
          ul: (p) => <ul className="my-2 list-disc space-y-1 pl-5" {...p} />,
          ol: (p) => <ol className="my-2 list-decimal space-y-1 pl-5" {...p} />,
          li: (p) => <li className="pl-0.5" {...p} />,
          strong: (p) => <strong className="font-semibold text-foreground" {...p} />,
          em: (p) => <em className="italic text-muted-foreground" {...p} />,
          hr: () => <hr className="my-4 border-border" />,
          a: (p) => <a className="text-brand underline underline-offset-2" target="_blank" rel="noreferrer" {...p} />,
          blockquote: (p) => (
            <blockquote className="my-3 rounded-r-md border-l-2 border-brand bg-muted/30 px-3 py-1.5 text-muted-foreground" {...p} />
          ),
          code: ({ className, children, ...p }) =>
            className ? (
              <code className="block overflow-x-auto rounded-md bg-muted/40 p-3 font-mono text-xs" {...p}>
                {children}
              </code>
            ) : (
              <code className="rounded bg-muted/50 px-1 py-0.5 font-mono text-xs" {...p}>
                {children}
              </code>
            ),
          pre: (p) => <pre className="my-3" {...p} />,
          table: (p) => (
            <div className="my-3 overflow-x-auto rounded-md border border-border">
              <table className="w-full border-collapse text-left text-xs" {...p} />
            </div>
          ),
          thead: (p) => <thead className="bg-muted/40" {...p} />,
          th: (p) => <th className="border-b border-border px-2.5 py-1.5 font-semibold" {...p} />,
          td: (p) => <td className="border-b border-border/60 px-2.5 py-1.5 align-top" {...p} />,
          input: (p) => <input className="mr-1.5 translate-y-[1px]" {...p} />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
