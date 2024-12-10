"use client";

import { ChatSection as ChatSectionUI } from "@llamaindex/chat-ui";
import "@llamaindex/chat-ui/styles/markdown.css";
import "@llamaindex/chat-ui/styles/pdf.css";
import { useChat } from "ai/react";
import CustomChatMessages from "@/components/ui/chat/chat-messages";
import { useClientConfig } from "@/components/ui/hooks/use-config";
import { MultimodalInput } from "@/components/ui/chat/custom-multi-modal-input";

export default function ChatSection() {
  const { backend } = useClientConfig();
  const handler = useChat({
    api: `${backend}/api/chat`,
    onError: (error: unknown) => {
      if (!(error instanceof Error)) throw error;
      let errorMessage: string;
      try {
        errorMessage = JSON.parse(error.message).detail;
      } catch (e) {
        errorMessage = error.message;
      }
      alert(errorMessage);
    },
  });

  return (
    <ChatSectionUI handler={handler} className="flex flex-col min-w-0 w-[90dvw] max-w-3xl h-[80dvh] mx-auto my-[10dvh] bg-background rounded-lg shadow-lg border p-10">
      <CustomChatMessages/>
      <MultimodalInput 
        chatId="chat"
        input={handler.input}
        setInput={handler.setInput}
        isLoading={handler.isLoading}
        stop={handler.stop}
        messages={handler.messages}
        setMessages={handler.setMessages}
        append={handler.append}
        handleSubmit={handler.handleSubmit}
      />
    </ChatSectionUI>
  );
}
