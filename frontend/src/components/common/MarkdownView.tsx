import React from "react";

interface MarkdownViewProps {
  content: string;
  className?: string;
}

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content, className = "" }) => {
  if (!content) return null;

  // Split content by sections or code blocks
  const renderFormattedText = (text: string) => {
    // Process markdown line by line
    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBlockLang = "";
    let codeBlockLines: string[] = [];
    let listItems: string[] = [];

    const flushList = (keyPrefix: string) => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`${keyPrefix}-list`} className="my-2 space-y-1 pl-5 list-disc text-slate-700 dark:text-slate-300">
            {listItems.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {parseInline(item)}
              </li>
            ))}
          </ul>
        );
        listItems = [];
      }
    };

    const flushCodeBlock = (keyPrefix: string) => {
      if (codeBlockLines.length > 0) {
        elements.push(
          <div
            key={`${keyPrefix}-code`}
            className="my-3 overflow-hidden rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-900 shadow-sm"
          >
            {codeBlockLang && (
              <div className="flex items-center justify-between px-3 py-1.5 bg-slate-800/80 border-b border-slate-700/60 text-[11px] font-mono text-slate-400">
                <span>{codeBlockLang}</span>
              </div>
            )}
            <pre className="p-3 text-xs font-mono text-emerald-400 overflow-x-auto leading-relaxed">
              <code>{codeBlockLines.join("\n")}</code>
            </pre>
          </div>
        );
        codeBlockLines = [];
      }
    };

    const parseInline = (lineText: string): React.ReactNode => {
      // Parse `inline code`, **bold**, *italic*
      const parts: React.ReactNode[] = [];
      let remaining = lineText;
      let key = 0;

      while (remaining.length > 0) {
        // Check inline code `code`
        const codeMatch = remaining.match(/^`([^`]+)`/);
        if (codeMatch) {
          parts.push(
            <code
              key={key++}
              className="rounded-md bg-slate-100 dark:bg-surface-800 border border-slate-200 dark:border-surface-700 px-1.5 py-0.5 font-mono text-xs font-semibold text-brand-600 dark:text-brand-400"
            >
              {codeMatch[1]}
            </code>
          );
          remaining = remaining.slice(codeMatch[0].length);
          continue;
        }

        // Check bold **text**
        const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/);
        if (boldMatch) {
          parts.push(
            <strong key={key++} className="font-bold text-slate-900 dark:text-white">
              {boldMatch[1]}
            </strong>
          );
          remaining = remaining.slice(boldMatch[0].length);
          continue;
        }

        // Check italic *text*
        const italicMatch = remaining.match(/^\*([^*]+)\*/);
        if (italicMatch) {
          parts.push(
            <em key={key++} className="italic text-slate-800 dark:text-slate-200">
              {italicMatch[1]}
            </em>
          );
          remaining = remaining.slice(italicMatch[0].length);
          continue;
        }

        // Plain text up to next special char
        const nextSpecial = remaining.search(/[`*]/);
        if (nextSpecial === -1) {
          parts.push(remaining);
          break;
        } else if (nextSpecial === 0) {
          // Special char wasn't a valid token, push it and move 1 char
          parts.push(remaining[0]);
          remaining = remaining.slice(1);
        } else {
          parts.push(remaining.slice(0, nextSpecial));
          remaining = remaining.slice(nextSpecial);
        }
      }

      return parts.length === 1 ? parts[0] : <>{parts}</>;
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();

      // Check code block fence ```
      if (trimmed.startsWith("```")) {
        flushList(`line-${index}`);
        if (inCodeBlock) {
          inCodeBlock = false;
          flushCodeBlock(`line-${index}`);
        } else {
          inCodeBlock = true;
          codeBlockLang = trimmed.slice(3).trim();
        }
        return;
      }

      if (inCodeBlock) {
        codeBlockLines.push(line);
        return;
      }

      // Check bullet lists
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        listItems.push(trimmed.slice(2));
        return;
      }

      // If not a list item, flush any pending list
      flushList(`line-${index}`);

      // Headings
      if (trimmed.startsWith("### ")) {
        elements.push(
          <h3
            key={index}
            className="text-sm font-bold text-slate-900 dark:text-white mt-4 mb-2 pb-1 border-b border-slate-200/80 dark:border-surface-800/80 flex items-center gap-1.5"
          >
            {parseInline(trimmed.slice(4))}
          </h3>
        );
        return;
      }

      if (trimmed.startsWith("## ")) {
        elements.push(
          <h2
            key={index}
            className="text-base font-bold text-slate-900 dark:text-white mt-5 mb-2 pb-1.5 border-b border-slate-200 dark:border-surface-800"
          >
            {parseInline(trimmed.slice(3))}
          </h2>
        );
        return;
      }

      if (trimmed.startsWith("# ")) {
        elements.push(
          <h1 key={index} className="text-lg font-extrabold text-slate-900 dark:text-white mt-5 mb-2">
            {parseInline(trimmed.slice(2))}
          </h1>
        );
        return;
      }

      // Callout / Quote
      if (trimmed.startsWith("> ")) {
        elements.push(
          <blockquote
            key={index}
            className="my-2 border-l-4 border-brand-500 bg-brand-50/50 dark:bg-brand-950/20 px-3.5 py-2 rounded-r-lg text-xs text-slate-700 dark:text-slate-300 italic"
          >
            {parseInline(trimmed.slice(2))}
          </blockquote>
        );
        return;
      }

      // Empty line
      if (!trimmed) {
        elements.push(<div key={index} className="h-1.5" />);
        return;
      }

      // Regular Paragraph
      elements.push(
        <p key={index} className="leading-relaxed text-slate-700 dark:text-slate-300">
          {parseInline(line)}
        </p>
      );
    });

    flushList("end");
    flushCodeBlock("end");

    return elements;
  };

  return <div className={`text-xs space-y-2 leading-relaxed ${className}`}>{renderFormattedText(content)}</div>;
};
