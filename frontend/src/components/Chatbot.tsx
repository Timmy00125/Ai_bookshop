import React, { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Bot, Sparkles } from "lucide-react";
import api from "../api";

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<
    { sender: "bot" | "user"; text: string }[]
  >([
    {
      sender: "bot",
      text: "Hi there! I am your AI Bookshop Assistant. Looking for a recommendation or have a specific topic in mind? Let me help!",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/ai/chat", { query: userMessage });
      setMessages((prev) => [...prev, { sender: "bot", text: res.data.reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "Oops! I am having trouble connecting to my knowledge base right now. Please try again later.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 lg:bottom-10 lg:right-10 w-16 h-16 bg-indigo-600 text-white rounded-full shadow-2xl hover:bg-indigo-700 hover:scale-110 active:scale-95 transition-all duration-300 flex items-center justify-center z-50 overflow-hidden group"
      >
        <div className="absolute inset-0 bg-white/20 blur-xl opacity-0 group-hover:opacity-100 transition duration-500 rounded-full"></div>
        <MessageSquare size={28} className="relative z-10" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 lg:bottom-10 lg:right-10 w-[380px] h-[550px] max-h-[80vh] bg-white rounded-3xl shadow-2xl shadow-indigo-900/10 border border-slate-100 flex flex-col z-50 overflow-hidden transform transition-all duration-300">
      {/* Header */}
      <div className="bg-indigo-600 p-4 px-6 flex justify-between items-center text-white relative overflow-hidden flex-shrink-0">
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl transform translate-x-1/2 -translate-y-1/2"></div>
        <div className="flex items-center gap-3 relative z-10">
          <div className="bg-white p-2 rounded-xl text-indigo-600 shadow-sm">
            <Bot size={24} />
          </div>
          <div>
            <h3 className="font-extrabold text-lg tracking-tight">
              AI Assistant
            </h3>
            <p className="text-indigo-200 text-xs font-medium flex items-center gap-1">
              <Sparkles size={10} /> Online
            </p>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-indigo-200 hover:text-white p-2 bg-indigo-700/50 hover:bg-indigo-700 rounded-full transition relative z-10"
        >
          <X size={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-grow overflow-y-auto p-5 pb-8 space-y-4 bg-slate-50 relative scroll-smooth">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"} group items-end gap-2`}
          >
            {msg.sender === "bot" && (
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mb-1 border border-indigo-200 text-indigo-600">
                <Bot size={16} />
              </div>
            )}
            <div
              className={`max-w-[75%] px-4 py-3 text-[15px] leading-relaxed relative ${
                msg.sender === "user"
                  ? "bg-indigo-600 text-white rounded-2xl rounded-tr-sm shadow-md shadow-indigo-600/10"
                  : "bg-white text-slate-700 rounded-2xl rounded-tl-sm shadow-sm border border-slate-100"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start items-end gap-2">
            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mb-1 border border-indigo-200 text-indigo-600">
              <Bot size={16} />
            </div>
            <div className="bg-white text-slate-500 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm border border-slate-100 max-w-[75%] flex space-x-1.5 items-center object-cover">
              <div className="w-2 h-2 bg-indigo-300 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSend}
        className="p-4 bg-white border-t border-slate-100 flex-shrink-0"
      >
        <div className="relative flex items-center group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything..."
            className="w-full bg-slate-50 border border-slate-200 rounded-full pl-5 pr-14 py-3.5 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition-all shadow-sm"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-1.5 bg-indigo-600 text-white p-2 rounded-full hover:bg-indigo-700 hover:shadow-md disabled:bg-slate-300 disabled:shadow-none transition-all active:scale-95"
          >
            <Send size={18} className="translate-x-[1px] translate-y-[-1px]" />
          </button>
        </div>
      </form>
    </div>
  );
}
