import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function sanitizeUIMessages(messages: any[]) {
  return messages.map(message => ({
    ...message,
    content: message.content.replace(/\n+/g, '\n').trim()
  }));
}

