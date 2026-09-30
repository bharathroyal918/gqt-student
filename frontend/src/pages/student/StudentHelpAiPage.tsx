import React, { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Sparkles,
  Send,
  Bot,
  User,
  Plus,
  Trash2,
  RotateCcw,
  Check,
  Copy,
  Terminal,
  MessageSquare,
  Search,
  Code2,
  AlertCircle,
  Lightbulb,
} from "lucide-react";
import {
  studentApi,
  AIConversationDetail,
  AIMessageItem,
} from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";

// Helper component for rich code block rendering with Copy functionality
const FormattedCodeBlock: React.FC<{ code: string; language?: string }> = ({
  code,
  language = "python",
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-surface-700 bg-surface-950 font-mono text-xs shadow-md">
      <div className="flex items-center justify-between px-3 py-1.5 bg-surface-800/80 border-b border-surface-700 text-slate-400">
        <span className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
          <Terminal className="h-3 w-3 text-brand-400" />
          {language || "code"}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-surface-700 transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-3.5 overflow-x-auto text-slate-100 leading-relaxed">
        <pre>
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
};

// Markdown & formatted content renderer for assistant messages
const MessageContentRenderer: React.FC<{ text: string }> = ({ text }) => {
  // Parse code blocks fenced with ```
  const parts: React.ReactNode[] = [];
  const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const regularText = text.substring(lastIndex, match.index);
      parts.push(<span key={`text-${lastIndex}`}>{renderSimpleFormatting(regularText)}</span>);
    }
    const lang = match[1] || "python";
    const codeContent = match[2];
    parts.push(
      <FormattedCodeBlock
        key={`code-${match.index}`}
        language={lang}
        code={codeContent.replace(/\n$/, "")}
      />
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(
      <span key={`text-${lastIndex}`}>{renderSimpleFormatting(text.substring(lastIndex))}</span>
    );
  }

  return <div className="space-y-1 text-xs leading-relaxed">{parts}</div>;
};

// Helper for bold, lists, and inline code formatting
function renderSimpleFormatting(content: string) {
  const lines = content.split("\n");
  return lines.map((line, idx) => {
    // Header styling
    if (line.startsWith("### ")) {
      return (
        <h4 key={idx} className="text-sm font-bold text-white mt-3 mb-1.5 flex items-center gap-1.5">
          {line.replace("### ", "")}
        </h4>
      );
    }
    if (line.startsWith("#### ")) {
      return (
        <h5 key={idx} className="text-xs font-bold text-brand-300 mt-2 mb-1">
          {line.replace("#### ", "")}
        </h5>
      );
    }
    // Bullet points
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      return (
        <div key={idx} className="flex items-start gap-1.5 ml-2 my-0.5 text-slate-300">
          <span className="text-brand-400 font-bold">•</span>
          <span>{parseInline(line.trim().substring(2))}</span>
        </div>
      );
    }
    // Numbered items
    const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
    if (numMatch) {
      return (
        <div key={idx} className="flex items-start gap-1.5 ml-2 my-0.5 text-slate-300">
          <span className="text-brand-400 font-semibold">{numMatch[1]}.</span>
          <span>{parseInline(numMatch[2])}</span>
        </div>
      );
    }

    if (!line.trim()) {
      return <div key={idx} className="h-1.5" />;
    }

    return (
      <p key={idx} className="my-0.5 text-slate-200">
        {parseInline(line)}
      </p>
    );
  });
}

function parseInline(text: string) {
  const parts: React.ReactNode[] = [];
  // match `inline code` or **bold**
  const inlineRegex = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let lastIdx = 0;
  let match: RegExpExecArray | null;

  while ((match = inlineRegex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index));
    }
    const token = match[0];
    if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code
          key={`code-${match.index}`}
          className="bg-surface-800 text-brand-300 px-1.5 py-0.5 rounded text-[11px] font-mono border border-surface-700"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={`bold-${match.index}`} className="font-semibold text-white">
          {token.slice(2, -2)}
        </strong>
      );
    }
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx));
  }
  return parts.length > 0 ? parts : text;
}

const SUGGESTED_QUESTIONS = [
  "How do I fix a RecursionError in Python?",
  "Explain Polymorphism in Python OOP with examples",
  "What is the difference between a List and a Tuple?",
  "How does Binary Search achieve O(log N) complexity?",
  "How do I merge two dictionaries in Python?",
];

export const StudentHelpAiPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [inputVal, setInputVal] = useState("");
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Fetch Conversations List
  const {
    data: conversations = [],
    isLoading: isListLoading,
    isError: isListError,
    refetch: refetchList,
  } = useQuery({
    queryKey: ["student", "ai", "conversations"],
    queryFn: studentApi.getAIConversations,
  });

  // Automatically select the first conversation if none selected
  useEffect(() => {
    if (!selectedConvId && conversations.length > 0) {
      setSelectedConvId(conversations[0].id);
    }
  }, [conversations, selectedConvId]);

  // 2. Fetch Active Conversation Details & Messages
  const {
    data: activeConversation,
    isLoading: isConvLoading,
  } = useQuery({
    queryKey: ["student", "ai", "conversation", selectedConvId],
    queryFn: () => studentApi.getAIConversationDetail(selectedConvId!),
    enabled: !!selectedConvId,
  });

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages]);

  // 3. Create Conversation Mutation
  const createConvMutation = useMutation({
    mutationFn: (initialMessage?: string) =>
      studentApi.createAIConversation({
        title: "New Consultation",
        initial_message: initialMessage,
      }),
    onSuccess: (newConv) => {
      queryClient.invalidateQueries({ queryKey: ["student", "ai", "conversations"] });
      setSelectedConvId(newConv.id);
      setInputVal("");
      setErrorBanner(null);
    },
    onError: (err: any) => {
      setErrorBanner(err?.response?.data?.error?.message || "Failed to start conversation.");
    },
  });

  // 4. Send Message Mutation
  const sendMsgMutation = useMutation({
    mutationFn: (content: string) => {
      if (!selectedConvId) throw new Error("No active conversation");
      return studentApi.sendAIMessage(selectedConvId, { content });
    },
    onMutate: async (content) => {
      setErrorBanner(null);
      // Optimistic update for student message
      await queryClient.cancelQueries({
        queryKey: ["student", "ai", "conversation", selectedConvId],
      });
      const previousConv = queryClient.getQueryData<AIConversationDetail>([
        "student",
        "ai",
        "conversation",
        selectedConvId,
      ]);

      if (previousConv) {
        const optimisticMsg: AIMessageItem = {
          id: `temp-${Date.now()}`,
          sender: "STUDENT",
          content,
          tokens_used: 0,
          created_at: new Date().toISOString(),
        };
        queryClient.setQueryData<AIConversationDetail>(
          ["student", "ai", "conversation", selectedConvId],
          {
            ...previousConv,
            messages: [...previousConv.messages, optimisticMsg],
          }
        );
      }
      return { previousConv };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["student", "ai", "conversation", selectedConvId],
      });
      queryClient.invalidateQueries({ queryKey: ["student", "ai", "conversations"] });
      setInputVal("");
    },
    onError: (err: any, _content, context) => {
      if (context?.previousConv) {
        queryClient.setQueryData(
          ["student", "ai", "conversation", selectedConvId],
          context.previousConv
        );
      }
      setErrorBanner(err?.response?.data?.error?.message || "Failed to send message.");
    },
  });

  // 5. Retry Mutation
  const retryMutation = useMutation({
    mutationFn: () => {
      if (!selectedConvId) throw new Error("No active conversation");
      return studentApi.retryAIMessage(selectedConvId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["student", "ai", "conversation", selectedConvId],
      });
      setErrorBanner(null);
    },
    onError: (err: any) => {
      setErrorBanner(err?.response?.data?.error?.message || "Failed to retry response.");
    },
  });

  // 6. Archive Conversation Mutation
  const archiveMutation = useMutation({
    mutationFn: (convId: string) => studentApi.archiveAIConversation(convId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student", "ai", "conversations"] });
      setSelectedConvId(null);
    },
  });

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    if (!selectedConvId) {
      createConvMutation.mutate(inputVal.trim());
    } else {
      sendMsgMutation.mutate(inputVal.trim());
    }
  };

  const handleStartWithPrompt = (prompt: string) => {
    if (!selectedConvId) {
      createConvMutation.mutate(prompt);
    } else {
      sendMsgMutation.mutate(prompt);
    }
  };

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const isGenerating = sendMsgMutation.isPending || retryMutation.isPending || createConvMutation.isPending;

  return (
    <div className="space-y-4 max-w-6xl mx-auto h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-brand-400" />
            AI Learning Mentor
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            24/7 intelligent tutoring, algorithmic hints, code debugging, and syntax explanations.
          </p>
        </div>
        <Badge variant="emerald" className="px-3 py-1 text-xs">
          Smart Pedagogical Tutor Online
        </Badge>
      </div>

      {/* Main Container: Sidebar + Chat Area */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-4 min-h-0">
        {/* Left Column: Conversation Sessions Sidebar (3.5 cols) */}
        <Card className="md:col-span-4 flex flex-col p-3 h-full border-surface-800 bg-surface-900/60 overflow-hidden">
          <div className="flex items-center justify-between gap-2 mb-3">
            <Button
              variant="primary"
              size="sm"
              className="w-full flex items-center justify-center gap-2 text-xs"
              onClick={() => createConvMutation.mutate(undefined)}
              disabled={createConvMutation.isPending}
            >
              <Plus className="h-4 w-4" />
              New Consultation
            </Button>
          </div>

          {/* Search bar */}
          <div className="relative mb-3">
            <Search className="h-3.5 w-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Filter history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-950/80 border border-surface-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {isListLoading ? (
              <div className="text-center py-8 text-xs text-slate-400">Loading consultations...</div>
            ) : isListError ? (
              <div className="p-3 text-center text-xs text-rose-400">
                Failed to load history.
                <button
                  onClick={() => refetchList()}
                  className="underline ml-1 text-brand-400 hover:text-brand-300"
                >
                  Retry
                </button>
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="text-center py-10 px-3 text-xs text-slate-500">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 text-slate-600 opacity-60" />
                No consultation history found. Start a new session above!
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const isSelected = conv.id === selectedConvId;
                return (
                  <div
                    key={conv.id}
                    onClick={() => setSelectedConvId(conv.id)}
                    className={`group relative flex items-center justify-between p-2.5 rounded-xl text-left cursor-pointer transition-all border ${
                      isSelected
                        ? "bg-brand-950/40 border-brand-500/50 text-white shadow-sm"
                        : "bg-surface-800/40 border-surface-700/40 text-slate-300 hover:bg-surface-800/80 hover:border-surface-600"
                    }`}
                  >
                    <div className="flex items-start gap-2.5 min-w-0 pr-2">
                      <Code2
                        className={`h-4 w-4 shrink-0 mt-0.5 ${
                          isSelected ? "text-brand-400" : "text-slate-500 group-hover:text-slate-400"
                        }`}
                      />
                      <div className="min-w-0">
                        <div className="text-xs font-semibold truncate">{conv.title}</div>
                        <div className="text-[11px] text-slate-400 truncate mt-0.5">
                          {conv.last_message_preview || "No messages yet"}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm("Archive this consultation session?")) {
                          archiveMutation.mutate(conv.id);
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 p-1 rounded transition-opacity"
                      title="Archive session"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </Card>

        {/* Right Column: Chat History & Input Area (8 cols) */}
        <Card className="md:col-span-8 flex flex-col p-4 h-full border-surface-800 bg-surface-900/60 overflow-hidden">
          {/* Active Conversation Top Banner */}
          <div className="flex items-center justify-between border-b border-surface-800 pb-3 mb-3">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-brand-900/40 border border-brand-700/50 flex items-center justify-center text-brand-400">
                <Bot className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">
                  {activeConversation?.title || "AI Consultation"}
                </h3>
                {activeConversation?.context_question_title && (
                  <span className="text-[11px] text-brand-400 flex items-center gap-1">
                    <Lightbulb className="h-3 w-3" /> Question:{" "}
                    {activeConversation.context_question_title}
                  </span>
                )}
              </div>
            </div>

            {activeConversation && (
              <Button
                variant="outline"
                size="sm"
                className="text-xs text-slate-400 hover:text-white"
                onClick={() => retryMutation.mutate()}
                disabled={isGenerating || (activeConversation?.messages?.length || 0) === 0}
                title="Regenerate last answer"
              >
                <RotateCcw className={`h-3 w-3 mr-1 ${retryMutation.isPending ? "animate-spin" : ""}`} />
                Retry
              </Button>
            )}
          </div>

          {/* Error Banner */}
          {errorBanner && (
            <div className="mb-3 p-2.5 bg-rose-950/60 border border-rose-800/80 rounded-xl text-rose-300 text-xs flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
                <span>{errorBanner}</span>
              </div>
              <button
                onClick={() => setErrorBanner(null)}
                className="text-rose-400 hover:text-rose-200 text-xs px-2 py-0.5 rounded"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {isConvLoading ? (
              <div className="flex items-center justify-center h-full text-xs text-slate-400">
                Loading session messages...
              </div>
            ) : !activeConversation || activeConversation.messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-4">
                <div className="h-12 w-12 rounded-2xl bg-brand-900/30 border border-brand-700/40 flex items-center justify-center text-brand-400 shadow-inner">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">How can I help you today?</h3>
                  <p className="text-xs text-slate-400 max-w-md mt-1">
                    Ask any question regarding programming, debugging exceptions, OOP concepts, or
                    algorithmic problem-solving.
                  </p>
                </div>

                {/* Quick Prompts */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg pt-2">
                  {SUGGESTED_QUESTIONS.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleStartWithPrompt(q)}
                      disabled={isGenerating}
                      className="text-left text-[11px] p-2.5 rounded-xl bg-surface-800/50 hover:bg-surface-800 border border-surface-700/60 text-slate-300 hover:text-white transition-all flex items-start gap-2 group"
                    >
                      <Lightbulb className="h-3.5 w-3.5 text-brand-400 shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                      <span className="line-clamp-2">{q}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              activeConversation.messages.map((m, idx) => {
                const isStudent = m.sender === "STUDENT";
                return (
                  <div
                    key={m.id || idx}
                    className={`flex items-start gap-3 ${
                      isStudent ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-bold shadow-sm ${
                        isStudent
                          ? "bg-brand-600 text-white"
                          : "bg-surface-800 text-brand-400 border border-surface-700"
                      }`}
                    >
                      {isStudent ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>

                    <div
                      className={`rounded-2xl p-4 text-xs max-w-2xl leading-relaxed shadow-sm ${
                        isStudent
                          ? "bg-brand-600 text-white rounded-tr-none"
                          : "bg-surface-900 border border-surface-800 text-slate-200 rounded-tl-none"
                      }`}
                    >
                      {isStudent ? (
                        <p className="whitespace-pre-wrap">{m.content}</p>
                      ) : (
                        <MessageContentRenderer text={m.content} />
                      )}
                    </div>
                  </div>
                );
              })
            )}

            {/* Typing Indicator */}
            {isGenerating && (
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-surface-800 text-brand-400 border border-surface-700">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-2xl rounded-tl-none p-3.5 bg-surface-900 border border-surface-800 text-slate-400 text-xs flex items-center gap-2">
                  <span className="flex gap-1">
                    <span className="h-2 w-2 rounded-full bg-brand-400 animate-bounce" />
                    <span
                      className="h-2 w-2 rounded-full bg-brand-400 animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                    <span
                      className="h-2 w-2 rounded-full bg-brand-400 animate-bounce"
                      style={{ animationDelay: "0.4s" }}
                    />
                  </span>
                  <span className="text-[11px] text-slate-400">Mentor is analyzing...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Input Form */}
          <form onSubmit={handleSendMessage} className="mt-3 pt-3 border-t border-surface-800 flex gap-2">
            <div className="relative flex-1">
              <textarea
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
                placeholder="Ask about Python code, error debugging, OOP concepts, or algorithms (Press Enter to send)..."
                rows={1}
                disabled={isGenerating}
                className="w-full bg-surface-950 border border-surface-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 resize-none min-h-[42px] max-h-[120px]"
              />
            </div>
            <Button
              type="submit"
              disabled={isGenerating || !inputVal.trim()}
              className="px-4 shrink-0 flex items-center justify-center gap-1.5 text-xs"
            >
              <Send className="h-4 w-4" />
              <span>Send</span>
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};
