'use client'

import Chat from "@/components/chat/chat-llama";

export default function Page() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-white">
        <div className="absolute inset-0 opacity-30 animate-gradient bg-gradient-to-r from-blue-100 via-purple-100 to-pink-100" 
             style={{ 
               backgroundSize: '400% 400%',
               animation: 'gradient 15s ease infinite'
             }}
        />
        <div className="absolute inset-0 opacity-20"
             style={{
               backgroundImage: `radial-gradient(circle at 50% 50%, 
                 rgba(255, 255, 255, 0.8) 0%, 
                 rgba(255, 255, 255, 0.3) 50%, 
                 transparent 100%)`
             }}
        />
      </div>

      {/* Chat component */}
      <div className="relative z-10">
        <Chat variant="standalone" />
      </div>
    </div>
  );
}

