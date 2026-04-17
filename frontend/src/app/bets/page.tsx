"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Flame, ExternalLink, Eye, LogIn, X } from "lucide-react";
import { api, type Bet, type SentimentData } from "@/lib/api";

export default function BetsPage() {
  const [bets, setBets] = useState<Bet[]>([]);
  const [sentiment, setSentiment] = useState<SentimentData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [b, s] = await Promise.allSettled([
        api.getBets(),
        api.getWsbSentiment({ spikes_only: "true", limit: "20" }),
      ]);
      if (b.status === "fulfilled") setBets(b.value);
      if (s.status === "fulfilled") setSentiment(s.value);
    } finally {
      setLoading(false);
    }
  }

  async function updateBetStatus(id: string, status: string) {
    await api.updateBet(id, { status });
    loadData();
  }

  function sentimentColor(score: number): string {
    if (score > 0.3) return "text-green-500";
    if (score > 0.05) return "text-green-400";
    if (score < -0.05) return "text-red-500";
    return "text-muted-foreground";
  }

  function sentimentLabel(score: number): string {
    if (score > 0.3) return "Very Bullish";
    if (score > 0.05) return "Bullish";
    if (score < -0.3) return "Very Bearish";
    if (score < -0.05) return "Bearish";
    return "Neutral";
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Flame className="h-8 w-8 text-orange-500" />
          Bets
        </h2>
        <p className="text-muted-foreground">
          Speculative opportunities from r/wallstreetbets sentiment. These are NOT part of your core strategy.
        </p>
      </div>

      <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4">
        <p className="text-sm text-orange-400">
          <strong>Disclaimer:</strong> Bets are sourced from WSB sentiment spikes and are inherently speculative.
          They are tracked separately from your TastyTrade-based strategies.
          Size appropriately and set strict risk limits.
        </p>
      </div>

      <Tabs defaultValue="spikes">
        <TabsList>
          <TabsTrigger value="spikes">Sentiment Spikes</TabsTrigger>
          <TabsTrigger value="tracked">Tracked Bets ({bets.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="spikes" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sentiment.length === 0 ? (
              <Card className="col-span-full">
                <CardContent className="pt-6">
                  <p className="text-muted-foreground text-center">
                    No sentiment spikes detected. The scraper runs every 30 minutes.
                  </p>
                </CardContent>
              </Card>
            ) : (
              sentiment.map((s) => (
                <Card key={s.id}>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center justify-between">
                      <span className="text-2xl font-bold">{s.symbol}</span>
                      <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/30">
                        Spike
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Mentions</span>
                        <p className="font-bold text-lg">{s.mention_count}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Sentiment</span>
                        <p className={`font-bold text-lg ${sentimentColor(s.avg_sentiment)}`}>
                          {s.avg_sentiment.toFixed(2)}
                        </p>
                      </div>
                    </div>
                    <p className={`text-sm font-medium ${sentimentColor(s.avg_sentiment)}`}>
                      {sentimentLabel(s.avg_sentiment)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Scraped: {new Date(s.scraped_at).toLocaleString()}
                    </p>
                    {s.top_posts && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">Top Posts:</p>
                        {((s.top_posts as Record<string, unknown>).posts as Array<{title: string; url: string; score: number}>)
                          ?.slice(0, 3)
                          .map((post, i) => (
                            <a
                              key={i}
                              href={post.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 text-xs text-blue-400 hover:underline truncate"
                            >
                              <ExternalLink className="h-3 w-3 shrink-0" />
                              <span className="truncate">{post.title}</span>
                              <span className="text-muted-foreground shrink-0">({post.score})</span>
                            </a>
                          ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="tracked" className="mt-4">
          <div className="space-y-4">
            {bets.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground text-center">
                    No tracked bets yet. The AI will flag opportunities from sentiment spikes.
                  </p>
                </CardContent>
              </Card>
            ) : (
              bets.map((bet) => (
                <Card key={bet.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <span className="text-2xl font-bold">{bet.symbol}</span>
                        <Badge variant={
                          bet.status === "watching" ? "secondary" :
                          bet.status === "entered" ? "default" :
                          "outline"
                        }>
                          {bet.status}
                        </Badge>
                        <span className={`text-sm font-medium ${sentimentColor(bet.sentiment_score)}`}>
                          Sentiment: {bet.sentiment_score.toFixed(2)}
                        </span>
                        {bet.mention_velocity && (
                          <span className="text-sm text-muted-foreground">
                            Velocity: {bet.mention_velocity.toFixed(1)}x
                          </span>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {bet.status === "watching" && (
                          <>
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => updateBetStatus(bet.id, "entered")}
                            >
                              <LogIn className="h-3 w-3 mr-1" />Enter
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => updateBetStatus(bet.id, "passed")}
                            >
                              <X className="h-3 w-3 mr-1" />Pass
                            </Button>
                          </>
                        )}
                        {bet.status === "entered" && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => updateBetStatus(bet.id, "closed")}
                          >
                            Close
                          </Button>
                        )}
                      </div>
                    </div>
                    {bet.notes && (
                      <p className="text-sm text-muted-foreground mt-2">{bet.notes}</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      Created: {new Date(bet.created_at).toLocaleString()}
                    </p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
