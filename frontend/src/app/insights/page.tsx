"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Brain, Send, Sparkles, Loader2 } from "lucide-react";
import { api, type InsightLog } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function InsightsPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [feed, setFeed] = useState<InsightLog[]>([]);
  const [generating, setGenerating] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getInsightFeed(10).then(setFeed).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || sending) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setSending(true);

    try {
      const res = await api.chat(userMsg);
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Failed to get response"}` },
      ]);
    } finally {
      setSending(false);
    }
  }

  async function handleGenerate() {
    setGenerating(true);
    try {
      await api.generateInsights();
      const updated = await api.getInsightFeed(10);
      setFeed(updated);
    } finally {
      setGenerating(false);
    }
  }

  const insightTypeLabel: Record<string, string> = {
    performance_review: "Performance",
    opportunity_scan: "Opportunities",
    wsb_scan: "WSB Scan",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">AI Insights</h2>
          <p className="text-muted-foreground">
            Chat with Claude about your portfolio, or review proactive insights
          </p>
        </div>
        <Button onClick={handleGenerate} disabled={generating} variant="secondary">
          <Sparkles className={`h-4 w-4 mr-2 ${generating ? "animate-pulse" : ""}`} />
          {generating ? "Generating..." : "Generate Insights"}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat */}
        <div className="lg:col-span-2">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Chat
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0">
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                  {messages.length === 0 && (
                    <div className="text-center text-muted-foreground py-12">
                      <Brain className="h-12 w-12 mx-auto mb-4 opacity-20" />
                      <p className="text-sm">
                        Ask about your trades, performance, or market opportunities.
                      </p>
                      <div className="mt-4 space-y-2">
                        {[
                          "How have my covered calls performed this month?",
                          "What TastyTrade setups look good right now?",
                          "Review my last 10 trades for patterns.",
                        ].map((q) => (
                          <button
                            key={q}
                            onClick={() => setInput(q)}
                            className="block mx-auto text-xs text-muted-foreground hover:text-foreground border border-border rounded-full px-4 py-1.5 transition-colors"
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm whitespace-pre-wrap ${
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        }`}
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {sending && (
                    <div className="flex justify-start">
                      <div className="bg-muted rounded-lg px-4 py-2.5">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                    </div>
                  )}
                  <div ref={scrollRef} />
                </div>
              </ScrollArea>
              <div className="flex gap-2 pt-4 mt-auto">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Ask about your trading performance..."
                  disabled={sending}
                />
                <Button onClick={handleSend} disabled={sending || !input.trim()} size="icon">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Insight Feed */}
        <Card className="h-[600px] flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle>Insight Feed</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 min-h-0">
            <ScrollArea className="h-full pr-4">
              <div className="space-y-4">
                {feed.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No insights yet. Click &ldquo;Generate Insights&rdquo; to run a proactive scan.
                  </p>
                ) : (
                  feed.map((insight) => (
                    <div key={insight.id} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {insightTypeLabel[insight.insight_type] || insight.insight_type}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(insight.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm line-clamp-6">{insight.content}</p>
                      <Separator />
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
