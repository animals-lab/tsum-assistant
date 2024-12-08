"use client";

import type { Message } from "ai";
import { motion } from "framer-motion";
import { SparklesIcon } from "./icons";
import { Markdown } from "./markdown";
import { PreviewAttachment } from "./preview-attachment";
import { cn } from "@/lib/utils";

export const PreviewMessage = ({
  message,
  chatId,
  isLoading,
}: {
  chatId: string;
  message: Message;
  isLoading: boolean;
}) => {
  console.log("Rendering message:", {
    role: message.role,
    content: message.content,
    id: message.id,
    data: (message as any).data,
  });

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
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
          {/* Regular message content */}
          {message.content && (
            <div className="flex flex-col gap-4">
              <Markdown>{message.content}</Markdown>
            </div>
          )}

          {/* Data parts from stream */}
          {(message as any).data?.map((item: any, index: number) => (
            <div key={index} className="flex flex-col gap-4">
              {item.messages?.map((msg: any, msgIndex: number) => (
                <div key={msgIndex}>
                  <Markdown>{msg.content}</Markdown>
                </div>
              ))}
              {item.text && <Markdown>{item.text}</Markdown>}
            </div>
          ))}

          {/* Tool invocations */}
          {(message as any).toolInvocations?.map((toolInvocation: any, index: number) => (
            <div key={toolInvocation.toolCallId} className="bg-muted p-4 rounded-lg">
              <div className="font-mono text-sm text-muted-foreground">
                Tool: {toolInvocation.toolName}
              </div>
              <div className="font-mono text-sm mt-2 text-muted-foreground">
                Arguments: {JSON.stringify(toolInvocation.args, null, 2)}
              </div>
              {'result' in toolInvocation && (
                <div className="font-mono text-sm mt-2 text-muted-foreground border-t border-muted-foreground/20 pt-2">
                  Result: {JSON.stringify(toolInvocation.result, null, 2)}
                </div>
              )}
            </div>
          ))}

          {/* Message annotations */}
          {(message as any).annotations?.map((annotation: any, index: number) => {
            if (annotation.type === "code") {
              return (
                <div key={annotation.id || index} className="bg-muted p-4 rounded-lg">
                  {annotation.language && (
                    <div className="font-mono text-sm text-muted-foreground mb-2">
                      {annotation.language}
                    </div>
                  )}
                  <pre className="font-mono text-sm whitespace-pre-wrap overflow-x-auto">
                    <code>{annotation.code}</code>
                  </pre>
                </div>
              );
            }

            if (annotation.type === "markdown") {
              return (
                <div key={annotation.id || index} className="prose dark:prose-invert max-w-none">
                  <Markdown>{annotation.content}</Markdown>
                </div>
              );
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
