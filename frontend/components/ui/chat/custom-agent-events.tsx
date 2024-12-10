import { AgentEventData } from '@llamaindex/chat-ui';
import { ChevronDown, Check } from 'lucide-react';
import { useMemo, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { TextShimmer } from '@/components/ui/core/text-shimmer';

interface ChatAgentEventsProps {
  data: AgentEventData[];
  isFinished: boolean;
}

interface GroupedEvents {
  agent: string;
  events: Array<{
    type: 'text' | 'progress';
    text?: string;
    progress?: {
      current: number;
      total: number;
    };
    isComplete: boolean;
  }>;
}

function ProgressBar({ current, total }: { current: number; total: number }) {
  const percentage = (current / total) * 100;
  return (
    <div className="w-full space-y-1.5 pl-6">
      <div className="flex justify-between text-xs text-gray-500">
        <span>Progress</span>
        <span>{Math.round(percentage)}%</span>
      </div>
      <div className="h-1 w-full bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          style={{ width: `${percentage}%` }}
          className="h-full bg-[#f8460f]"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  );
}

export function CustomChatAgentEvents({ data, isFinished }: ChatAgentEventsProps) {
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});
  
  const groupedEvents = useMemo(() => {
    const groups: Record<string, GroupedEvents> = {};
    
    data.forEach((event, index) => {
      if (!groups[event.agent]) {
        groups[event.agent] = {
          agent: event.agent,
          events: []
        };
      }

      const currentEvents = groups[event.agent].events;

      if (event.type === 'text') {
        currentEvents.push({
          type: 'text',
          text: event.text,
          isComplete: index !== data.length - 1 || isFinished
        });
      } else if (event.type === 'progress' && event.data) {
        const progressEvent = currentEvents.find(e => e.type === 'progress');
        if (progressEvent) {
          progressEvent.progress = event.data;
          progressEvent.isComplete = event.data.current === event.data.total;
        } else {
          currentEvents.push({
            type: 'progress',
            progress: event.data,
            isComplete: event.data.current === event.data.total
          });
        }
      }
    });

    return Object.values(groups);
  }, [data, isFinished]);

  useEffect(() => {
    const newCollapsedState: Record<string, boolean> = {};
    groupedEvents.forEach(group => {
      const isComplete = group.events.every(e => e.isComplete);
      const hasIncomplete = group.events.some(e => !e.isComplete);
      newCollapsedState[group.agent] = isComplete && !hasIncomplete;
    });
    setCollapsedSections(newCollapsedState);
  }, [groupedEvents]);

  if (!data.length) return null;

  const toggleSection = (agent: string) => {
    setCollapsedSections(prev => ({
      ...prev,
      [agent]: !prev[agent]
    }));
  };

  return (
    <div className="rounded-lg border border-gray-100 relative bg-white/70">
      {/* Main vertical timeline line - now outside of sections */}
      <div className="absolute left-[1.45rem] top-4 bottom-4 w-px bg-gray-100" />
      
      {groupedEvents.map((group, groupIndex) => {
        const isCollapsed = collapsedSections[group.agent];
        const isComplete = group.events.every(e => e.isComplete);
        
        return (
          <div key={`${group.agent}-${groupIndex}`} className="relative">
            {/* Section header */}
            <div 
              className="flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-gray-50 rounded-lg"
              onClick={() => toggleSection(group.agent)}
            >
              <div className="flex items-center gap-2">
                <div className="relative h-4 w-4 z-10">
                  {isComplete ? (
                    <div className="h-full w-full rounded-full bg-gray-100 flex items-center justify-center">
                      <Check className="h-2.5 w-2.5 text-gray-500" />
                    </div>
                  ) : (
                    <>
                      <div className="absolute inset-0 rounded-full bg-[#f8460f] animate-pulse" />
                      <div className="absolute inset-[3px] rounded-full bg-white" />
                      <div className="absolute inset-[5px] rounded-full bg-[#f8460f]" />
                    </>
                  )}
                </div>
                <span className="text-[#f8460f] font-medium">{group.agent}</span>
              </div>
              <motion.div
                animate={{ rotate: isCollapsed ? 0 : 180 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="h-5 w-5 text-gray-400" />
              </motion.div>
            </div>

            {/* Section content */}
            <AnimatePresence>
              {!isCollapsed && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div className="px-4 pb-3">
                    {/* Events list */}
                    <div className="space-y-2">
                      {group.events.map((event, eventIndex) => (
                        <motion.div 
                          key={eventIndex}
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: eventIndex * 0.1 }}
                        >
                          {event.type === 'text' && (
                            <div className="pl-6 pr-2 py-1">
                              {event.isComplete ? (
                                <span className="text-sm text-gray-600">{event.text}</span>
                              ) : (
                                <TextShimmer 
                                  className="text-sm"
                                  duration={1.5}
                                  spread={1.5}
                                >
                                  {event.text || ''}
                                </TextShimmer>
                              )}
                            </div>
                          )}
                          {event.type === 'progress' && event.progress && (
                            <ProgressBar 
                              current={event.progress.current} 
                              total={event.progress.total} 
                            />
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Section divider that doesn't cross the vertical line and has right margin */}
            {groupIndex < groupedEvents.length - 1 && (
              <div className="mx-[2.25rem] mr-4 border-t border-gray-100" />
            )}
          </div>
        );
      })}
    </div>
  );
} 