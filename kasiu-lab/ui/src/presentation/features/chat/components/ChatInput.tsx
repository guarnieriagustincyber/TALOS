import React from "react";
import { PromptBox } from "@/components/ui/prompt-box";

export interface ChatInputProps {
  activeScope: string;
  isThinking: boolean;
  isStreaming: boolean;
  onSend: (text: string) => void;
  onStop?: () => void;
  onClearHistory?: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  isThinking,
  isStreaming,
  onSend,
  onStop,
}) => {
  return (
    <div className="px-4 sm:px-8 md:px-14 lg:px-20 pb-4 sm:pb-6 md:pb-8 pt-2 shrink-0">
      <div className="w-full max-w-[980px] mx-auto">
        <PromptBox
          onSend={(msg) => onSend(msg)}
          placeholder="Pregunta a TALOS o ingresa un comando socrático..."
          isThinking={isThinking}
          isStreaming={isStreaming}
          onStop={onStop}
        />
      </div>
    </div>
  );
};

export default ChatInput;
