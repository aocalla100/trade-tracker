"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Brain,
  Flame,
  RefreshCw,
} from "lucide-react";
import { api, type Trade, type Position, type InsightLog, type SentimentData } from "@/lib/api";

export default function Dashboard() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [insights, setInsights] = useState<InsightLog[]>([]);
  const [spikes, setSpikes] = useState<SentimentData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const [t, p, i, s] = await Promise.allSettled([
        api.getTrades({ limit: "5", status: "open" }),
        api.getPositions(),
        api.getInsightFeed(5),
        api.getWsbSentiment({ spikes_only: "true", limit: "5" }),
      ]);
      if (t.status === "fulfilled") setTrades(t.value);
      if (p.status === "fulfilled") setPositions(p.value);
      if (i.status === "fulfilled") setInsights(i.value);
      if (s.status === "fulfilled") setSpikes(s.value);
    } finally {
      setLoading(false);
    }
  }

  const totalValue = positions.reduce((sum, p) => sum + (p.current_value || 0), 0);
  const totalUnrealized = positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
  const openTradeCount = trades.length;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">Portfolio overview and latest insights</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadDashboard} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Portfolio Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${totalValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Unrealized P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold flex items-center gap-2 ${totalUnrealized >= 0 ? "text-green-500" : "text-red-500"}`}>
              {totalUnrealized >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
              ${Math.abs(totalUnrealized).toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Open Trades
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" />
              {openTradeCount}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Core Positions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{positions.length}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Latest AI Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {insights.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No insights yet. Generate some from the AI Insights page.
              </p>
            ) : (
              insights.map((insight) => (
                <div key={insight.id} className="border-b border-border pb-3 last:border-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="secondary">{insight.insight_type}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(insight.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm line-clamp-3">{insight.content}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* WSB Spike Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-orange-500" />
              WSB Sentiment Spikes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {spikes.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No sentiment spikes detected recently.
              </p>
            ) : (
              spikes.map((spike) => (
                <div key={spike.id} className="flex items-center justify-between border-b border-border pb-3 last:border-0">
                  <div>
                    <span className="font-bold text-lg">{spike.symbol}</span>
                    <p className="text-xs text-muted-foreground">
                      {spike.mention_count} mentions &middot; Sentiment: {spike.avg_sentiment.toFixed(2)}
                    </p>
                  </div>
                  <Badge variant={spike.avg_sentiment > 0.2 ? "default" : "secondary"}>
                    {spike.avg_sentiment > 0.2 ? "Bullish" : "Neutral"}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Open Trades */}
      <Card>
        <CardHeader>
          <CardTitle>Open Trades</CardTitle>
        </CardHeader>
        <CardContent>
          {trades.length === 0 ? (
            <p className="text-sm text-muted-foreground">No open trades.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 font-medium text-muted-foreground">Symbol</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Strategy</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Direction</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">Entry</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">Qty</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((t) => (
                    <tr key={t.id} className="border-b border-border last:border-0">
                      <td className="py-2 font-medium">{t.underlying_symbol}</td>
                      <td className="py-2">{t.strategy_name}</td>
                      <td className="py-2">
                        <Badge variant={t.direction === "long" ? "default" : "secondary"}>
                          {t.direction}
                        </Badge>
                      </td>
                      <td className="py-2 text-right">${t.entry_price.toFixed(2)}</td>
                      <td className="py-2 text-right">{t.quantity}</td>
                      <td className="py-2 text-muted-foreground">
                        {new Date(t.entry_timestamp).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
