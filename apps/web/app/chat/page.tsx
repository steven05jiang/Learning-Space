"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useMock } from "@/lib/mock/hooks";
import { mockMessages } from "@/lib/mock";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  isProgress?: boolean;  // agent is still working — show inline progress row
  isStreaming?: boolean; // final response is being streamed — show blinking cursor
}

const MOCK_RESPONSES = [
  "I can help you explore your learning resources! What would you like to know?",
  "Based on your resources, you have materials covering machine learning, transformers, and knowledge graphs. Would you like a summary of any topic?",
  "Great question! I can help you find connections between your resources or suggest related topics.",
  "I've analyzed your learning collection. You seem to be focused on AI/ML topics. Would you like recommendations?",
];

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi! I'm your learning assistant. I can help you explore and find resources in your library.\n\nTry asking me:",
};

const EXAMPLE_PROMPTS = [
  "What are the key ideas across my saved resources?",
  "What should I read next based on what I've saved?",
  "Summarize what I've been learning recently",
  "What gaps exist in my current knowledge collection?",
];

function RainbowBotIcon() {
  return (
    <div className="relative h-8 w-8 shrink-0">
      <div
        className="absolute inset-0 animate-spin rounded-full"
        style={{
          background:
            "conic-gradient(from 0deg, #f43f5e, #f97316, #eab308, #22c55e, #3b82f6, #a855f7, #f43f5e)",
        }}
      />
      <div className="absolute inset-[2px] flex items-center justify-center rounded-full bg-background text-primary">
        <Bot className="h-4 w-4" />
      </div>
    </div>
  );
}

export default function ChatPage() {
  const isMock = useMock();

  const initialMessages: Message[] = isMock
    ? mockMessages.map((m) => ({ id: m.id, role: m.role, content: m.content }))
    : [WELCOME_MESSAGE];

  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const showExamples = messages.length === 1 && messages[0].id === "welcome";
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mockResponseIndex = useRef(0);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const resizeTextarea = useCallback(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
    setIsLoading(true);

    if (isMock) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      const response =
        MOCK_RESPONSES[mockResponseIndex.current % MOCK_RESPONSES.length];
      mockResponseIndex.current++;
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: "assistant", content: response },
      ]);
    } else {
      const progressId = (Date.now() + 1).toString();
      setMessages((prev) => [
        ...prev,
        { id: progressId, role: "assistant", content: "Thinking...", isProgress: true },
      ]);

      try {
        const token = localStorage.getItem("auth_token");
        const apiBase =
          process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

        const requestBody: { message: string; conversation_id?: string } = {
          message: userMessage.content,
        };
        if (conversationId) requestBody.conversation_id = conversationId;

        const res = await fetch(`${apiBase}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(requestBody),
        });

        if (res.status === 401) {
          window.location.href = "/login";
          return;
        }
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let responseStarted = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (raw === "[DONE]") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === progressId ? { ...m, isStreaming: false } : m,
                ),
              );
              break;
            }

            try {
              const event = JSON.parse(raw);
              if (event.conversation_id) setConversationId(event.conversation_id);

              if (event.type === "progress") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === progressId
                      ? { ...m, content: event.content, isProgress: true, isStreaming: false }
                      : m,
                  ),
                );
              } else if (event.type === "response") {
                if (!responseStarted) {
                  responseStarted = true;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === progressId
                        ? { ...m, content: event.content ?? "", isProgress: false, isStreaming: true }
                        : m,
                    ),
                  );
                } else {
                  // Append subsequent chunks for token-by-token streaming
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === progressId
                        ? { ...m, content: m.content + (event.content ?? ""), isStreaming: true }
                        : m,
                    ),
                  );
                }
              } else if (event.type === "error") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === progressId
                      ? { ...m, content: event.content ?? "An error occurred.", isProgress: false, isStreaming: false }
                      : m,
                  ),
                );
              }
            } catch {
              // skip malformed event lines
            }
          }
        }
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === progressId
              ? {
                  ...m,
                  content: "Sorry, I couldn't reach the AI service. Please try again.",
                  isProgress: false,
                  isStreaming: false,
                }
              : m,
          ),
        );
      }

      // Ensure streaming flag is cleared when stream ends
      setMessages((prev) =>
        prev.map((m) =>
          m.id === progressId ? { ...m, isStreaming: false, isProgress: false } : m,
        ),
      );
    }

    setIsLoading(false);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages */}
      <ScrollArea className="min-h-0 flex-1 p-4">
        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          {messages.map((message) =>
            message.isProgress ? (
              // Inline progress row: rainbow icon + progress text on one line, no bubble
              <div key={message.id} className="flex items-center gap-3">
                <RainbowBotIcon />
                <span className="text-sm italic text-muted-foreground">
                  {message.content}
                </span>
              </div>
            ) : (
              <div
                key={message.id}
                className={cn(
                  "flex gap-3",
                  message.role === "user" && "flex-row-reverse",
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                    message.role === "assistant"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  {message.role === "assistant" ? (
                    <Bot className="h-4 w-4" />
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                </div>
                <div
                  className={cn(
                    "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                    message.role === "assistant"
                      ? "w-full bg-muted text-foreground"
                      : "max-w-[75%] bg-primary text-primary-foreground",
                  )}
                >
                  {message.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none overflow-x-auto dark:prose-invert prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-headings:my-2">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                      </ReactMarkdown>
                      {message.isStreaming && (
                        <span className="inline-block h-4 w-0.5 animate-pulse bg-foreground align-middle" />
                      )}
                    </div>
                  ) : (
                    message.content
                  )}
                </div>
              </div>
            ),
          )}
          {/* Mock mode loading dots */}
          {isLoading && isMock && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-1 rounded-2xl bg-muted px-4 py-2.5">
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
              </div>
            </div>
          )}
          {showExamples && (
            <div className="flex flex-col gap-2 pl-11">
              {EXAMPLE_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setInput(prompt)}
                  className="rounded-xl border border-border bg-background px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t border-border p-4">
        <form
          onSubmit={handleSubmit}
          className="mx-auto flex max-w-3xl items-end gap-2"
        >
          <textarea
            ref={inputRef}
            value={input}
            rows={1}
            onChange={(e) => {
              setInput(e.target.value);
              resizeTextarea();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask about your resources..."
            disabled={isLoading}
            className="flex-1 resize-none overflow-hidden rounded-2xl bg-muted/50 px-4 py-2 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50 max-h-40 overflow-y-auto"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="h-9 w-9 shrink-0 rounded-full"
          >
            <Send className="h-4 w-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </form>
      </div>
    </div>
  );
}
