import { SourceData } from "@llamaindex/chat-ui";
import { Markdown as MarkdownUI } from "@llamaindex/chat-ui/widgets";
import { useClientConfig } from "@/hooks/use-config";
import { cn } from "@/lib/utils";

const preprocessMedia = (content: string) => {
  // Remove `sandbox:` from the beginning of the URL before rendering markdown
  // OpenAI models sometimes prepend `sandbox:` to relative URLs - this fixes it
  return content.replace(/(sandbox|attachment|snt):/g, "");
};

export function Markdown({
  content,
  sources,
  className,
}: {
  content: string;
  sources?: SourceData;
  className?: string;
}) {
  const { backend } = useClientConfig();
  const processedContent = preprocessMedia(content);
  return (
    <div className={cn("prose dark:prose-invert max-w-none", 
      "[&_img]:max-h-[150px] [&_img]:max-w-[300px] [&_img]:object-contain",
      "[&_a]:text-[#f8460f] [&_a]:font-normal [&_a:hover]:opacity-80 [&_a]:transition-opacity [&_a]:no-underline",
      className
    )}>
      <MarkdownUI
        content={processedContent}
        backend={backend}
        sources={sources}
      />
    </div>
  );
}
