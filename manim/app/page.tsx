/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import type React from "react";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useChat } from "ai/react";
import { Moon, Sun, Download, Video, FileText, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";

type Chat = {
  id: string;
  title: string;
  messages: any[];
};

export default function ChatInterface() {
  const [isDark, setIsDark] = useState(false);
  const [isInitialView, setIsInitialView] = useState(true);
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string>("");

  const { messages, input, handleInputChange, handleSubmit, setMessages } =
    useChat();

  // Initialize with a new chat
  useEffect(() => {
    if (chats.length === 0) {
      createNewChat();
    }
  }, [chats.length]);

  // Handle Ctrl+N for new chat
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "n") {
        e.preventDefault();
        createNewChat();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const createNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: "New Chat",
      messages: [],
    };
    setChats((prev) => [...prev, newChat]);
    setCurrentChatId(newChat.id);
    setMessages([]);
    setIsInitialView(true);
  };

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isInitialView) setIsInitialView(false);

    // Update chat title with first message if it's still "New Chat"
    if (chats.find((c) => c.id === currentChatId)?.title === "New Chat") {
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? { ...chat, title: input.slice(0, 30) + "..." }
            : chat
        )
      );
    }

    handleSubmit(e);

    // Update messages in chat history
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === currentChatId ? { ...chat, messages } : chat
      )
    );
  };

  return (
    <div className={`min-h-screen ${isDark ? "dark" : ""}`}>
      <div className="bg-background text-foreground transition-colors duration-300">
        <div className="flex-1 flex flex-col h-screen">
          <nav className="flex justify-between items-center p-4 border-b">
            <Button variant="ghost" size="icon" onClick={toggleTheme}>
              {isDark ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>
          </nav>

          <main className="flex-1 overflow-hidden">
            <AnimatePresence>
              {isInitialView ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="flex flex-col items-center justify-center h-full"
                >
                  <h1 className="text-4xl font-bold mb-8">
                    What do you want to learn today ?
                  </h1>
                  <form onSubmit={onSubmit} className="w-full max-w-2xl px-4">
                    <Input
                      value={input}
                      onChange={handleInputChange}
                      placeholder="Ask anything... "
                      className="h-12 text-lg"
                    />
                  </form>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 h-full overflow-auto"
                >
                  <div className="flex flex-col h-full">
                    <Tabs
                      defaultValue="conceptual"
                      className="flex-1 flex flex-col"
                    >
                      <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="conceptual">
                          Conceptual Chat
                        </TabsTrigger>
                        <TabsTrigger value="technical">
                          Technical Chat
                        </TabsTrigger>
                      </TabsList>
                      <TabsContent
                        value="conceptual"
                        className="flex-1 overflow-auto"
                      >
                        <div className="space-y-4 p-4">
                          {messages.map((message) => (
                            <motion.div
                              key={message.id}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className={`flex ${
                                message.role === "user"
                                  ? "justify-end"
                                  : "justify-start"
                              }`}
                            >
                              <div
                                className={`max-w-[80%] rounded-lg p-4 ${
                                  message.role === "user"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted"
                                }`}
                              >
                                {message.content}
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </TabsContent>
                      <TabsContent
                        value="technical"
                        className="flex-1 overflow-auto"
                      >
                        <div className="p-4">
                          Technical chat content here...
                        </div>
                      </TabsContent>
                    </Tabs>
                    <form onSubmit={onSubmit} className="p-4 border-t">
                      <Input
                        value={input}
                        onChange={handleInputChange}
                        placeholder="Type your message..."
                      />
                    </form>
                  </div>

                  <div className="flex flex-col h-full gap-4 overflow-auto">
                    <Card className="flex-1">
                      <div className="p-4 flex justify-between items-center border-b">
                        <div className="flex items-center gap-2">
                          <Video className="h-5 w-5" />
                          <span>Video Player</span>
                        </div>
                        <Button variant="ghost" size="icon">
                          <Download className="h-5 w-5" />
                        </Button>
                      </div>
                      <div className="aspect-video bg-muted" />
                    </Card>

                    <Card className="flex-1">
                      <div className="p-4 flex justify-between items-center border-b">
                        <div className="flex items-center gap-2">
                          <FileText className="h-5 w-5" />
                          <span>Transcript</span>
                        </div>
                        <Button variant="ghost" size="icon">
                          <Download className="h-5 w-5" />
                        </Button>
                      </div>
                      <div className="p-4 h-[200px] overflow-auto">
                        Transcript content here...
                      </div>
                    </Card>

                    <Card>
                      <div className="p-4 flex justify-between items-center border-b">
                        <div className="flex items-center gap-2">
                          <Volume2 className="h-5 w-5" />
                          <span>Audio</span>
                        </div>
                        <Button variant="ghost" size="icon">
                          <Download className="h-5 w-5" />
                        </Button>
                      </div>
                      <div className="p-4">Audio controls here...</div>
                    </Card>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>
      </div>
    </div>
  );
}
