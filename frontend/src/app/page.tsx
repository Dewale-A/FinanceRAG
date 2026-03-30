"use client";

import { useState, useRef, useEffect } from "react";
import { Send, FileText, Upload, BarChart3, Clock, Shield, Loader2 } from "lucide-react";

// Use local proxy to avoid mixed content (HTTPS frontend -> HTTP backend)
const PROXY_URL = "/api/proxy";

interface Source {
  filename: string;
  chunk_index: number;
  relevance_score: number;
  preview: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  model?: string;
  responseTime?: number;
  documentsRetrieved?: number;
}

interface Stats {
  collection_name: string;
  document_count: number;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [showKeyInput, setShowKeyInput] = useState(true);
  const [stats, setStats] = useState<Stats | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "upload" | "history">("chat");
  const [uploadStatus, setUploadStatus] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem("financerag-api-key");
    if (saved) {
      setApiKey(saved);
      setShowKeyInput(false);
    }
    fetchStats();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${PROXY_URL}?endpoint=/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error("Failed to fetch stats:", e);
    }
  };

  const saveKey = () => {
    localStorage.setItem("financerag-api-key", apiKey);
    setShowKeyInput(false);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const startTime = Date.now();

    try {
      const res = await fetch(PROXY_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ endpoint: "/query", apiKey, question: input, k: 5 }),
      });

      if (res.status === 403) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Invalid API key. Please check your key and try again.",
          },
        ]);
        setShowKeyInput(true);
        return;
      }

      const data = await res.json();
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        model: data.model,
        responseTime: parseFloat(elapsed),
        documentsRetrieved: data.documents_retrieved,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Failed to connect to the API. Please check that the server is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus("Uploading...");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        headers: { "X-API-Key": apiKey },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadStatus(`Ingested ${file.name}: ${data.chunks_created} chunks created`);
        fetchStats();
      } else {
        setUploadStatus("Upload failed. Check your API key.");
      }
    } catch (e) {
      setUploadStatus("Upload failed. Server unreachable.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-[#1a1a2e] text-white px-6 py-4 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-7 h-7 text-teal-400" />
            <div>
              <h1 className="text-xl font-bold tracking-tight">FinanceRAG</h1>
              <p className="text-xs text-gray-400">Financial Document Q&A</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <nav className="flex gap-1">
              <button
                onClick={() => setActiveTab("chat")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  activeTab === "chat"
                    ? "bg-teal-500/20 text-teal-400"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setActiveTab("upload")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  activeTab === "upload"
                    ? "bg-teal-500/20 text-teal-400"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Upload
              </button>
            </nav>
            {stats && (
              <div className="text-xs text-gray-400 flex items-center gap-1">
                <BarChart3 className="w-3 h-3" />
                {stats.document_count} chunks
              </div>
            )}
            <button
              onClick={() => setShowKeyInput(true)}
              className="text-gray-400 hover:text-white"
              title="API Key Settings"
            >
              <Shield className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* API Key Modal */}
      {showKeyInput && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Enter API Key</h2>
            <p className="text-sm text-gray-500 mb-4">
              Your API key is stored locally in your browser and never sent to third parties.
            </p>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your X-API-Key..."
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm"
              onKeyDown={(e) => e.key === "Enter" && saveKey()}
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={saveKey}
                className="flex-1 bg-[#1a1a2e] text-white py-3 rounded-xl text-sm font-medium hover:bg-[#2a2a4e] transition"
              >
                Save Key
              </button>
              {apiKey && (
                <button
                  onClick={() => setShowKeyInput(false)}
                  className="px-6 py-3 text-gray-500 text-sm hover:text-gray-700"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-6">
        {activeTab === "chat" ? (
          <div className="flex flex-col h-[calc(100vh-180px)]">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-6 pb-4">
              {messages.length === 0 && (
                <div className="text-center py-20">
                  <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-gray-800 mb-2">
                    Ask anything about your financial documents
                  </h2>
                  <p className="text-gray-500 max-w-md mx-auto mb-8">
                    Query regulatory documents, compliance policies, and risk
                    management frameworks using natural language.
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {[
                      "What are the Basel III capital requirements?",
                      "Explain our AML compliance policy",
                      "What is the credit risk assessment process?",
                      "Data governance policy for sensitive data",
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => {
                          setInput(q);
                        }}
                        className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:border-teal-400 hover:text-teal-600 transition"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] ${
                      msg.role === "user"
                        ? "bg-[#1a1a2e] text-white rounded-2xl rounded-br-md px-5 py-3"
                        : "bg-white border border-gray-200 rounded-2xl rounded-bl-md px-5 py-4 shadow-sm"
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                    {/* Sources */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-100">
                        <p className="text-xs font-semibold text-gray-500 mb-2">Sources</p>
                        <div className="space-y-2">
                          {msg.sources.map((s, j) => (
                            <div
                              key={j}
                              className="bg-gray-50 rounded-lg px-3 py-2 text-xs"
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium text-gray-700">
                                  {s.filename}
                                </span>
                                <span
                                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                    s.relevance_score > 0.7
                                      ? "bg-green-100 text-green-700"
                                      : s.relevance_score > 0.5
                                      ? "bg-amber-100 text-amber-700"
                                      : "bg-gray-100 text-gray-600"
                                  }`}
                                >
                                  {(s.relevance_score * 100).toFixed(0)}%
                                </span>
                              </div>
                              <p className="text-gray-500 line-clamp-2">{s.preview}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    {msg.model && (
                      <div className="mt-3 flex items-center gap-3 text-[10px] text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {msg.responseTime}s
                        </span>
                        <span>{msg.documentsRetrieved} docs retrieved</span>
                        <span>{msg.model}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-5 py-4 shadow-sm">
                    <Loader2 className="w-5 h-5 text-teal-500 animate-spin" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 pt-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Ask a question about your financial documents..."
                  className="flex-1 px-5 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm"
                  disabled={loading}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="px-5 py-3 bg-[#1a1a2e] text-white rounded-xl hover:bg-[#2a2a4e] transition disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Upload Tab */
          <div className="max-w-2xl mx-auto py-10">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Upload Documents</h2>
            <p className="text-sm text-gray-500 mb-6">
              Upload financial documents to add to the knowledge base. Supports PDF, DOCX, TXT, and MD files.
            </p>

            <label className="block border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center hover:border-teal-400 transition cursor-pointer">
              <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <p className="text-sm text-gray-600 font-medium">
                Drag and drop a file here, or click to browse
              </p>
              <p className="text-xs text-gray-400 mt-1">PDF, DOCX, TXT, MD</p>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleUpload}
                className="hidden"
              />
            </label>

            {uploadStatus && (
              <div className="mt-4 p-4 bg-teal-50 border border-teal-200 rounded-xl text-sm text-teal-700">
                {uploadStatus}
              </div>
            )}

            {stats && (
              <div className="mt-8 bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Collection Stats</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-[#1a1a2e]">{stats.document_count}</p>
                    <p className="text-xs text-gray-500 mt-1">Total Chunks</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-[#1a1a2e]">{stats.collection_name}</p>
                    <p className="text-xs text-gray-500 mt-1">Collection</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-4 text-center text-xs text-gray-400">
        Powered by <a href="https://veristack.ca" className="text-teal-500 hover:underline">VeriStack</a> | FinanceRAG v1.0
      </footer>
    </div>
  );
}
