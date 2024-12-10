import { useChatMessage } from "@llamaindex/chat-ui";
import { User2 } from "lucide-react";
import { SparklesIcon } from "@/components/ui/icons";

export function ChatMessageAvatar() {
  const { message } = useChatMessage();
  if (message.role === "user") {
    // return (
    //   <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-muted">
    //     <User2 className="h-4 w-4" />
    //   </div>
    // );
  }

  return (
    <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full border bg-black text-white">
      <SparklesIcon size={16} />
    </div>
  );
}
