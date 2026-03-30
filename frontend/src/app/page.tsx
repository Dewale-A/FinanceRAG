"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  FileText,
  Upload,
  BarChart3,
  Clock,
  Shield,
  ShieldCheck,
  Database,
  Zap,
  BookOpen,
  Search,
  ChevronRight,
  X,
} from "lucide-react";

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
  const [activeTab, setActiveTab] = useState<"chat" | "upload" | "analytics">("chat");
  const [analytics, setAnalytics] = useState<any>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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

  const fetchAnalytics = async () => {
    try {
      const res = await fetch(`${PROXY_URL}?endpoint=/analytics`);
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (e) {
      console.error("Failed to fetch analytics:", e);
    }
  };

  const saveKey = () => {
    localStorage.setItem("financerag-api-key", apiKey);
    setShowKeyInput(false);
    inputRef.current?.focus();
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const question = input;
    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const startTime = Date.now();

    try {
      const res = await fetch(PROXY_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: "/query", apiKey, question, k: 5 }),
      });

      if (res.status === 403) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "Authentication failed. Please check your API key and try again.",
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
          content:
            "Unable to reach the API. Please verify the server is running and try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadStatus("Processing...");
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
        setUploadStatus(
          `Successfully ingested "${file.name}" into ${data.chunks_created} chunks`
        );
        fetchStats();
      } else {
        setUploadStatus("Upload failed. Please check your API key.");
      }
    } catch (e) {
      setUploadStatus("Upload failed. Server unreachable.");
    }
  };

  const suggestedQuestions = [
    {
      icon: <ShieldCheck className="w-4 h-4" />,
      text: "What are the Basel III capital requirements?",
    },
    {
      icon: <Search className="w-4 h-4" />,
      text: "Explain our AML compliance policy",
    },
    {
      icon: <Database className="w-4 h-4" />,
      text: "Data governance policy for sensitive data",
    },
    {
      icon: <Zap className="w-4 h-4" />,
      text: "Credit risk assessment process",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-[#0f172a] text-white border-b border-slate-700/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight">
                  Finance<span className="text-teal-400">RAG</span>
                </h1>
                <p className="text-[10px] text-slate-400 tracking-wide uppercase">
                  Document Intelligence
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <nav className="flex bg-slate-800/50 rounded-lg p-0.5">
                <button
                  onClick={() => setActiveTab("chat")}
                  className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
                    activeTab === "chat"
                      ? "bg-teal-500/20 text-teal-400 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveTab("upload")}
                  className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
                    activeTab === "upload"
                      ? "bg-teal-500/20 text-teal-400 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Upload
                </button>
                <button
                  onClick={() => { setActiveTab("analytics"); fetchAnalytics(); }}
                  className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
                    activeTab === "analytics"
                      ? "bg-teal-500/20 text-teal-400 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Analytics
                </button>
              </nav>

              {stats && (
                <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/50 rounded-lg">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[11px] text-slate-400">
                    {stats.document_count} chunks indexed
                  </span>
                </div>
              )}

              <button
                onClick={() => setShowKeyInput(true)}
                className="p-2 text-slate-400 hover:text-teal-400 transition"
                title="API Key Settings"
              >
                <Shield className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* API Key Modal */}
      {showKeyInput && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl border border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  Authentication
                </h2>
                <p className="text-xs text-gray-500">
                  Enter your API key to continue
                </p>
              </div>
            </div>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key..."
              className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white text-sm transition"
              onKeyDown={(e) => e.key === "Enter" && saveKey()}
            />
            <p className="text-[11px] text-gray-400 mt-2 ml-1">
              Stored locally in your browser. Never sent to third parties.
            </p>
            <div className="flex gap-3 mt-5">
              <button
                onClick={saveKey}
                disabled={!apiKey}
                className="flex-1 bg-gradient-to-r from-[#0f172a] to-[#1e293b] text-white py-3 rounded-xl text-sm font-semibold hover:shadow-lg transition disabled:opacity-40"
              >
                Continue
              </button>
              {apiKey && (
                <button
                  onClick={() => setShowKeyInput(false)}
                  className="px-5 py-3 text-gray-400 text-sm hover:text-gray-600 transition"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Source Detail Panel */}
      {selectedSource && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-40">
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-teal-500" />
                <h3 className="font-semibold text-gray-900 text-sm">
                  {selectedSource.filename}
                </h3>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="p-1 hover:bg-gray-100 rounded-lg transition"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-sm text-gray-700 leading-relaxed">
                {selectedSource.preview}
              </p>
            </div>
            <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
              <span>
                Relevance:{" "}
                <span className="font-semibold text-teal-600">
                  {(selectedSource.relevance_score * 100).toFixed(0)}%
                </span>
              </span>
              <span>Chunk #{selectedSource.chunk_index}</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 py-6">
        {activeTab === "chat" && (
          <div className="flex flex-col h-[calc(100vh-180px)]">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto pb-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full">
                  <div className="text-center max-w-lg">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-teal-50 to-cyan-50 flex items-center justify-center mx-auto mb-6 shadow-sm border border-teal-100">
                      <BookOpen className="w-10 h-10 text-teal-500" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                      Financial Document{" "}
                      <span className="gradient-text">Intelligence</span>
                    </h2>
                    <p className="text-sm text-gray-500 mb-10 leading-relaxed">
                      Ask questions about regulatory documents, compliance
                      policies, and risk frameworks. Powered by AI with source
                      attribution.
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {suggestedQuestions.map((q, i) => (
                        <button
                          key={i}
                          onClick={() => setInput(q.text)}
                          className="flex items-center gap-3 px-4 py-3.5 bg-white border border-gray-200 rounded-xl text-left text-sm text-gray-600 hover:border-teal-300 hover:shadow-md hover:shadow-teal-500/5 transition-all group"
                        >
                          <span className="text-gray-400 group-hover:text-teal-500 transition">
                            {q.icon}
                          </span>
                          <span className="flex-1">{q.text}</span>
                          <ChevronRight className="w-3 h-3 text-gray-300 group-hover:text-teal-400 transition" />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-5">
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${
                        msg.role === "user" ? "justify-end" : "justify-start"
                      } message-enter`}
                    >
                      <div
                        className={`max-w-[85%] ${
                          msg.role === "user"
                            ? "bg-gradient-to-br from-[#0f172a] to-[#1e293b] text-white rounded-2xl rounded-br-sm px-5 py-3.5 shadow-lg shadow-slate-900/10"
                            : "bg-white border border-gray-200/80 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm"
                        }`}
                      >
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {msg.content}
                        </p>

                        {/* Sources */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-gray-100">
                            <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2.5">
                              Sources
                            </p>
                            <div className="space-y-2">
                              {msg.sources.map((s, j) => (
                                <button
                                  key={j}
                                  onClick={() => setSelectedSource(s)}
                                  className="w-full text-left bg-gray-50 hover:bg-teal-50/50 rounded-xl px-4 py-3 text-xs transition-all group border border-transparent hover:border-teal-200"
                                >
                                  <div className="flex items-center justify-between mb-1.5">
                                    <div className="flex items-center gap-2">
                                      <FileText className="w-3.5 h-3.5 text-gray-400 group-hover:text-teal-500 transition" />
                                      <span className="font-semibold text-gray-700">
                                        {s.filename}
                                      </span>
                                    </div>
                                    <span
                                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                        s.relevance_score > 0.7
                                          ? "bg-emerald-100 text-emerald-700"
                                          : s.relevance_score > 0.5
                                          ? "bg-amber-100 text-amber-700"
                                          : "bg-gray-100 text-gray-600"
                                      }`}
                                    >
                                      {(s.relevance_score * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <p className="text-gray-500 line-clamp-2 leading-relaxed">
                                    {s.preview}
                                  </p>
                                </button>
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
                            <span className="w-1 h-1 rounded-full bg-gray-300" />
                            <span>
                              {msg.documentsRetrieved} sources
                            </span>
                            <span className="w-1 h-1 rounded-full bg-gray-300" />
                            <span>{msg.model}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="flex justify-start message-enter">
                      <div className="bg-white border border-gray-200/80 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full bg-teal-500 loading-dot" />
                          <div className="w-2 h-2 rounded-full bg-teal-500 loading-dot" />
                          <div className="w-2 h-2 rounded-full bg-teal-500 loading-dot" />
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Input */}
            <div className="pt-4">
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                    placeholder="Ask a question about your financial documents..."
                    className="w-full px-5 py-3.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent text-sm shadow-sm placeholder:text-gray-400 pr-12"
                    disabled={loading}
                  />
                </div>
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="px-5 py-3.5 bg-gradient-to-r from-teal-500 to-teal-600 text-white rounded-xl hover:shadow-lg hover:shadow-teal-500/25 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}
        {activeTab === "upload" && (
          /* Upload Tab */
          <div className="max-w-2xl mx-auto py-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center">
                <Upload className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  Document Ingestion
                </h2>
                <p className="text-xs text-gray-500">
                  Upload financial documents to the knowledge base
                </p>
              </div>
            </div>

            <label className="block border-2 border-dashed border-gray-300 rounded-2xl p-16 text-center hover:border-teal-400 hover:bg-teal-50/30 transition-all cursor-pointer group">
              <div className="w-14 h-14 rounded-2xl bg-gray-100 group-hover:bg-teal-100 flex items-center justify-center mx-auto mb-4 transition">
                <Upload className="w-7 h-7 text-gray-400 group-hover:text-teal-500 transition" />
              </div>
              <p className="text-sm font-medium text-gray-700 mb-1">
                Drop a file here or click to browse
              </p>
              <p className="text-xs text-gray-400">
                Supports PDF, DOCX, TXT, and MD files
              </p>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleUpload}
                className="hidden"
              />
            </label>

            {uploadStatus && (
              <div className="mt-4 p-4 bg-teal-50 border border-teal-200 rounded-xl text-sm text-teal-700 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-teal-500" />
                {uploadStatus}
              </div>
            )}

            {stats && (
              <div className="mt-8 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                  Knowledge Base
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-xl p-5 text-center border border-gray-100">
                    <p className="text-3xl font-bold text-[#0f172a]">
                      {stats.document_count}
                    </p>
                    <p className="text-xs text-gray-500 mt-1 font-medium">
                      Chunks Indexed
                    </p>
                  </div>
                  <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-xl p-5 text-center border border-gray-100">
                    <p className="text-3xl font-bold text-[#0f172a]">5</p>
                    <p className="text-xs text-gray-500 mt-1 font-medium">
                      Documents
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        {activeTab === "analytics" && (
          /* Analytics Tab */
          <div className="max-w-3xl mx-auto py-10">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Analytics</h2>
                <p className="text-xs text-gray-500">
                  Query performance and usage insights
                </p>
              </div>
            </div>

            {analytics ? (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm text-center">
                    <p className="text-3xl font-bold text-[#0f172a]">
                      {analytics.total_queries}
                    </p>
                    <p className="text-xs text-gray-500 mt-1 font-medium">
                      Total Queries
                    </p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm text-center">
                    <p className="text-3xl font-bold text-[#0f172a]">
                      {(analytics.avg_response_time_ms / 1000).toFixed(1)}s
                    </p>
                    <p className="text-xs text-gray-500 mt-1 font-medium">
                      Avg Response Time
                    </p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm text-center">
                    <p className="text-3xl font-bold text-[#0f172a]">
                      {analytics.avg_docs_retrieved}
                    </p>
                    <p className="text-xs text-gray-500 mt-1 font-medium">
                      Avg Sources Retrieved
                    </p>
                  </div>
                </div>

                {/* Recent Queries Table */}
                <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-100">
                    <h3 className="text-sm font-semibold text-gray-700">
                      Recent Queries
                    </h3>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {analytics.recent_queries.length > 0 ? (
                      analytics.recent_queries.map((q: any) => (
                        <div
                          key={q.id}
                          className="px-6 py-4 hover:bg-gray-50/50 transition"
                        >
                          <p className="text-sm text-gray-800 font-medium mb-1.5">
                            {q.question}
                          </p>
                          <div className="flex items-center gap-3 text-[11px] text-gray-400">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {q.response_time_ms
                                ? `${(q.response_time_ms / 1000).toFixed(1)}s`
                                : "N/A"}
                            </span>
                            <span className="w-1 h-1 rounded-full bg-gray-300" />
                            <span>{q.documents_retrieved} sources</span>
                            <span className="w-1 h-1 rounded-full bg-gray-300" />
                            <span>{q.model}</span>
                            <span className="w-1 h-1 rounded-full bg-gray-300" />
                            <span>
                              {q.timestamp
                                ? new Date(q.timestamp).toLocaleDateString(
                                    "en-US",
                                    {
                                      month: "short",
                                      day: "numeric",
                                      hour: "2-digit",
                                      minute: "2-digit",
                                    }
                                  )
                                : ""}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="px-6 py-12 text-center text-sm text-gray-400">
                        No queries logged yet. Ask a question to get started.
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-20 text-sm text-gray-400">
                Loading analytics...
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200/80 py-4">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between">
          <p className="text-[11px] text-gray-400">
            Powered by{" "}
            <a
              href="https://veristack.ca"
              className="text-teal-500 hover:text-teal-600 font-medium transition"
              target="_blank"
              rel="noopener noreferrer"
            >
              VeriStack
            </a>
          </p>
          <p className="text-[11px] text-gray-400">
            FinanceRAG v1.0 | AI-Powered Document Intelligence
          </p>
        </div>
      </footer>
    </div>
  );
}
