// flashcard-tool-ui/app/docchat/page.tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  FileText,
  Download,
  Copy,
  Send,
  Loader2,
  ChevronLeft,
  AlertTriangle,
  Trash2,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { Toaster } from "@/components/ui/toaster";
import { generateMetadocument } from "@/lib/chatService";

interface Message {
  id: string;
  text: string;
  sender: "user" | "system";
  isProcessing?: boolean;
  isError?: boolean;
}

export default function DocumentChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "div[data-radix-scroll-area-viewport]",
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  };

  // Auto-adjust textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (inputValue.trim() === "" || isSending) return;

    const userMessageText = inputValue;
    const userMessage: Message = {
      id: Date.now().toString(),
      text: userMessageText,
      sender: "user",
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsSending(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const processingMessageId = `processing-${Date.now()}`;
    const processingMessage: Message = {
      id: processingMessageId,
      text: "Thinking...",
      sender: "system",
      isProcessing: true,
    };
    setMessages((prev) => [...prev, processingMessage]);
    scrollToBottom();

    try {
      const metadocument = await generateMetadocument(userMessageText);
      const systemMessage: Message = {
        id: `system-${Date.now()}`,
        text: metadocument,
        sender: "system",
      };
      setMessages((prev) =>
        prev
          .filter((msg) => msg.id !== processingMessageId)
          .concat(systemMessage),
      );
    } catch (error: any) {
      console.error("Error fetching metadocument:", error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        text: "Error",
        sender: "system",
        isError: true,
      };
      setMessages((prev) =>
        prev
          .filter((msg) => msg.id !== processingMessageId)
          .concat(errorMessage),
      );
      toast({
        title: "API Error",
        description:
          error.message ||
          "Failed to get response from the document chat service.",
        variant: "destructive",
      });
    } finally {
      setIsSending(false);
      scrollToBottom();
    }
  };

  const handleCopyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: "Copied to clipboard!",
        description: "The system's response has been copied.",
      });
    } catch (err) {
      toast({
        title: "Failed to copy",
        description: "Could not copy to clipboard. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleDownloadText = (text: string) => {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "memcard_chat_response.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: "Download started",
      description: "The system's response is being downloaded.",
    });
  };

  const handleBackToActions = () => {
    router.push("/actions");
  };

  const handleClearChat = () => {
    setMessages([]);
    setInputValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    toast({
      title: "Chat Cleared",
      description: "The current chat session has been cleared.",
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
      <Toaster />
      <Card className="w-full max-w-4xl h-[calc(100vh-8rem)] sm:h-[calc(100vh-4rem)] md:h-[85vh] bg-[#FAF9F7] rounded-3xl shadow-lg flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b flex justify-between items-center bg-white">
          <h1 className="text-xl font-semibold">Document Chat</h1>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearChat}
              className="font-semibold text-xs sm:text-sm"
              title="Clear Chat"
            >
              <Trash2 className="h-3.5 w-3.5 sm:mr-1" />
              <span className="hidden sm:inline">Clear</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackToActions}
              className="font-semibold text-xs sm:text-sm"
            >
              <ChevronLeft className="h-3.5 w-3.5 sm:mr-1" />
              <span className="hidden sm:inline">Actions</span>
            </Button>
          </div>
        </div>

        {/* Chat Area */}
        <ScrollArea
          className="flex-grow p-4 space-y-4 bg-[#FAF9F7]"
          ref={scrollAreaRef}
        >
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex mb-3 ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.sender === "user" ? (
                <div className="bg-blue-600 text-white p-3 rounded-xl max-w-[75%] shadow">
                  <p className="text-base whitespace-pre-wrap break-words">
                    {message.text}
                  </p>
                </div>
              ) : (
                <Card
                  className={`p-3 rounded-xl max-w-[75%] bg-white border shadow ${
                    message.isError ? "border-red-500 bg-red-50" : "bg-gray-50"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {message.isError ? (
                      <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                    ) : (
                      <FileText className="h-5 w-5 text-gray-500 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-grow">
                      {message.isProcessing ? (
                        <div className="flex items-center space-x-2">
                          <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                          <p className="text-sm text-gray-500">
                            {message.text}
                          </p>
                        </div>
                      ) : (
                        <p
                          className={`text-base whitespace-pre-wrap break-words ${
                            message.isError
                              ? "text-red-700 font-semibold"
                              : "text-gray-800"
                          }`}
                        >
                          {message.text}
                        </p>
                      )}
                    </div>
                  </div>
                  {!message.isProcessing && !message.isError && (
                    <div className="mt-2 pt-2 border-t flex items-center justify-end space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-7 px-2"
                        onClick={() => handleCopyToClipboard(message.text)}
                      >
                        <Copy className="h-3 w-3 mr-1" />
                        Copy
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-7 px-2"
                        onClick={() => handleDownloadText(message.text)}
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Download
                      </Button>
                    </div>
                  )}
                </Card>
              )}
            </div>
          ))}
          {messages.length === 0 && (
            <div className="text-center text-gray-500 pt-10">
              Start the conversation by typing your question below.
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 border-t bg-white">
          <div className="flex items-end space-x-2">
            {" "}
            <Textarea
              ref={textareaRef}
              placeholder="Ask something... (Shift + Enter for new line)"
              className="flex-grow rounded-lg text-base p-2.5 resize-none min-h-[44px] max-h-[150px] overflow-y-auto"
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={isSending}
              rows={1}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isSending || inputValue.trim() === ""}
              className="rounded-full h-11 w-11 flex-shrink-0"
              size="icon"
              type="submit"
            >
              {isSending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
