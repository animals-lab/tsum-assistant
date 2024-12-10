import { ChatMessage, ChatMessages, useChatUI, getAnnotationData, MessageAnnotationType, Message } from "@llamaindex/chat-ui";
import { CustomChatAgentEvents } from "./custom-agent-events";
import { ChatMessageAvatar } from "./chat-avatar";
import { CustomMessageContent } from "./custom-message-content";

export function CustomChatMessages() {
  const { messages, isLoading } = useChatUI();
  
  return (
    <ChatMessages className="flex-1 flex flex-col overflow-hidden bg-transparent">
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: rgba(0, 0, 0, 0.2);
          border-radius: 2px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: rgba(0, 0, 0, 0.3);
        }
      `}</style>
      <ChatMessages.List className="flex-1 overflow-y-auto px-4 py-6 space-y-6 custom-scrollbar">
        {messages.map((message: Message, index: number) => {
          const agentEvents = getAnnotationData(message.annotations, MessageAnnotationType.AGENT_EVENTS);
          const isLast = index === messages.length - 1;
          
          return (
            <ChatMessage 
              key={index} 
              message={message} 
              isLast={isLast}
            >
              <div className="flex flex-col space-y-4 w-full">
                {/* Regular message (user or assistant without events) */}
                {(!message.isUser && !agentEvents.length) || message.isUser ? (
                  <div className={`flex items-start space-x-3 ${message.role === 'user' ? 'justify-end' : ''}`}>
                    {message.role !== 'user' && <ChatMessageAvatar />}
                    <div className={`${message.role === 'user' ? '!bg-[#808080] text-white' : 'bg-transparent text-gray-900'} flex-initial rounded-2xl p-4`}>
                      <CustomMessageContent />
                    </div>
                  </div>
                ) : null}

                {/* Agent message with events */}
                {message.role !== 'user' && agentEvents.length > 0 && (
                  <div className="flex items-start space-x-3">
                    <ChatMessageAvatar />
                    <div className="flex-1">
                      <div className="flex-1 mb-6">
                        <CustomChatAgentEvents 
                          data={agentEvents}
                          isFinished={!isLoading || !isLast}
                        />
                      </div>
                      <div className="bg-transparent rounded-2xl p-4">
                        <CustomMessageContent />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ChatMessage>
          );
        })}
      </ChatMessages.List>
      {isLoading && (
        <div className="flex justify-center p-4">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-[#f8460f] border-t-transparent" />
        </div>
      )}
    </ChatMessages>
  );
} 