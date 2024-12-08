"use client";

import type { Message } from "ai";
import { motion } from "framer-motion";
import { SparklesIcon } from "./icons";
import { Markdown } from "./markdown";
import { PreviewAttachment } from "./preview-attachment";
import { cn } from "@/lib/utils";

interface MessagePart {
  type: 'text' | 'tool' | 'annotation';
  content: any;
  order: number;
  messageId?: string;
}

export const PreviewMessage = ({
  message,
  chatId,
  isLoading,
}: {
  chatId: string;
  message: Message;
  isLoading: boolean;
}) => {
  console.log("Message:", {
    id: message.id,
    role: message.role,
    content: message.content,
    annotations: (message as any).annotations?.map((a: any) => ({
      type: a.type,
      messageId: a.messageId,
      id: a.id
    })),
    toolInvocations: (message as any).toolInvocations?.map((t: any) => ({
      id: t.toolCallId,
      messageId: t.messageId,
      name: t.toolName
    }))
  });

  // Organize message parts in correct sequence
  const messageParts: MessagePart[] = [];
  let order = 0;

  // Add text content first
  if (message.content) {
    messageParts.push({
      type: 'text',
      content: message.content,
      order: order++,
      messageId: message.id
    });
  }

  // Add tool invocations next
  if ((message as any).toolInvocations) {
    (message as any).toolInvocations.forEach((tool: any) => {
      messageParts.push({
        type: 'tool',
        content: tool,
        order: order++,
        messageId: message.id
      });
    });
  }

  // Add annotations
  if ((message as any).annotations) {
    (message as any).annotations.forEach((annotation: any) => {
      messageParts.push({
        type: 'annotation',
        content: annotation,
        order: order++,
        messageId: message.id
      });
    });
  }

  // Sort parts by order
  const sortedParts = messageParts.sort((a, b) => a.order - b.order);

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
      {/* Debug info */}
      <div className="text-xs text-slate-500 mb-2 font-mono">
        Message ID: {message.id}
        <br />
        Parts: {sortedParts.map(p => p.type).join(', ')}
      </div>

      <div
        className={cn(
          "group-data-[role=user]/message:bg-primary group-data-[role=user]/message:text-primary-foreground flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl",
        )}
      >
        {message.role === "assistant" && (
          <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
            <SparklesIcon size={14} />
          </div>
        )}

        <div className="flex flex-col gap-2 w-full">
          {sortedParts.map((part, index) => {
            if (part.type === 'text') {
              return (
                <div key={`text-${index}`} className="flex flex-col gap-4">
                  <Markdown>{part.content}</Markdown>
                </div>
              );
            }

            if (part.type === 'tool') {
              const toolInvocation = part.content;
              return (
                <div key={`tool-${toolInvocation.toolCallId}`} 
                  className="bg-slate-50 p-4 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="text-xs text-slate-400 mb-1">Tool ID: {toolInvocation.toolCallId}</div>
                  <div className="font-mono text-sm text-slate-700 flex items-center gap-2 mb-1">
                    <div className="size-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="font-semibold">Tool:</span> {toolInvocation.toolName}
                  </div>
                  <div className="font-mono text-sm mt-3 bg-white p-3 rounded border border-slate-100">
                    <div className="text-slate-600">
                      <span className="font-semibold text-slate-700">Arguments:</span>
                      <pre className="mt-1 text-slate-600 whitespace-pre-wrap break-all hyphens-auto">{JSON.stringify(toolInvocation.args, null, 2)}</pre>
                    </div>
                    {'result' in toolInvocation && (
                      <div className="mt-3 pt-3 border-t border-slate-100">
                        <span className="font-semibold text-slate-700">Result:</span>
                        <pre className="mt-1 text-slate-600 whitespace-pre-wrap break-all hyphens-auto">{JSON.stringify(toolInvocation.result, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                </div>
              );
            }

            if (part.type === 'annotation') {
              const annotation = part.content;
              if (annotation.type === "code") {
                return (
                  <div key={`code-${annotation.id || index}`} className="bg-[#1e1e1e] p-4 rounded-lg border border-[#323232] shadow-sm">
                    <div className="text-xs text-[#858585] mb-1">Annotation ID: {annotation.id}</div>
                    {annotation.language && (
                      <div className="font-mono text-sm text-[#858585] mb-2 flex items-center justify-between">
                        <span>{annotation.language}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-[#323232] text-[#858585]">VS Code Dark+</span>
                      </div>
                    )}
                    <pre className="font-mono text-sm whitespace-pre-wrap overflow-x-auto break-all">
                      <code className="text-[#d4d4d4] [&_.keyword]:text-[#569cd6] [&_.string]:text-[#ce9178] [&_.function]:text-[#dcdcaa] [&_.number]:text-[#b5cea8] [&_.comment]:text-[#6a9955] hyphens-auto break-words">
                        {annotation.code}
                      </code>
                    </pre>
                  </div>
                );
              }

              if (annotation.type === "markdown") {
                return (
                  <div key={`markdown-${annotation.id || index}`} className="prose dark:prose-invert max-w-none">
                    <div className="text-xs text-slate-400 mb-1">Annotation ID: {annotation.id}</div>
                    <Markdown>{annotation.content}</Markdown>
                  </div>
                );
              }
            }

            return null;
          })}

          {message.experimental_attachments && (
            <div className="flex flex-row gap-2">
              {message.experimental_attachments.map((attachment) => (
                <PreviewAttachment
                  key={attachment.url}
                  attachment={attachment}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export const ThinkingMessage = () => {
  const role = "assistant";

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div
        className={cn(
          "flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl",
          {
            "group-data-[role=user]/message:bg-muted": true,
          },
        )}
      >
        <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
          <SparklesIcon size={14} />
        </div>

        <div className="flex flex-col gap-2 w-full">
          <div className="flex flex-col gap-4 text-muted-foreground">
            Thinking...
          </div>
        </div>
      </div>
    </motion.div>
  );
};
