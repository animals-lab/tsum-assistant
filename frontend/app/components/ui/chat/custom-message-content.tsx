import { useChatMessage } from "@llamaindex/chat-ui";
import { Markdown } from "../custom/markdown";

export function CustomMessageContent() {
  const { message } = useChatMessage();

  return (
    <div className="prose prose-sm max-w-none">
      <Markdown content={message.content} />
    </div>
  );
} 