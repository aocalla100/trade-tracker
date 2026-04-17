"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { api, type StrategyAnalysis, type BehaviorAnalysis } from "@/lib/api";

const COLORS = ["#22c55e", "#ef4444", "#3b82f6", "#f59e0b", "#8b5cf6", "#ec4899"];

export default function AnalyticsPage() {
  const [strategies, setStrategies] = useState<StrategyAnalysis[]>([]);
  const [behavior, setBehavior] = useState<BehaviorAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [s, b] = await Promise.allSettled([
          api.getStrategyAnalysis(),
          api.getBehaviorAnalysis(),
        ]);
        if (s.status === "fulfilled") setStrategies(s.value);
        if (b.status === "fulfilled") setBehavior(b.value);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const pnlData = strategies.map((s) => ({
    name: s.strategy_name,
    pnl: s.total_pnl,
    trades: s.total_trades,
  }));

  const winRateData = strategies.map((s) => ({
    name: s.strategy_name,
    "Win Rate": s.win_rate,
    Expectancy: s.expectancy,
  }));

  const behaviorPie = behavior
    ? [
        { name: "On Time", value: behavior.on_time_exits },
        { name: "Early", value: behavior.early_exits },
        { name: "Late", value: behavior.late_exits },
      ].filter((d) => d.value > 0)
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Performance Analytics</h2>
        <p className="text-muted-foreground">
          Strategy analysis, Greeks insights, and behavioral patterns
        </p>
      </div>

      <Tabs defaultValue="strategy">
        <TabsList>
          <TabsTrigger value="strategy">Strategy</TabsTrigger>
          <TabsTrigger value="behavior">Behavior</TabsTrigger>
        </TabsList>

        <TabsContent value="strategy" className="space-y-6 mt-4">
          {/* Strategy Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {strategies.map((s) => (
              <Card key={s.strategy_name}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">{s.strategy_name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Win Rate</span>
                    <span className="font-medium">{s.win_rate}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Expectancy</span>
                    <span className={`font-medium ${s.expectancy >= 0 ? "text-green-500" : "text-red-500"}`}>
                      ${s.expectancy.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total P&L</span>
                    <span className={`font-medium ${s.total_pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                      ${s.total_pnl.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Trades</span>
                    <span>{s.total_trades} ({s.wins}W / {s.losses}L)</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* P&L Chart */}
          {pnlData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Total P&L by Strategy</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={pnlData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Bar dataKey="pnl" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Win Rate Chart */}
          {winRateData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Win Rate & Expectancy</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={winRateData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="Win Rate" fill="#22c55e" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Expectancy" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {strategies.length === 0 && !loading && (
            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground text-center">
                  No closed trades yet. Analytics will appear here once you close some trades.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="behavior" className="space-y-6 mt-4">
          {behavior && behavior.total_trades > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Plan Adherence</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <div className="text-5xl font-bold">
                      {behavior.plan_adherence_rate ?? 0}%
                    </div>
                    <p className="text-muted-foreground mt-2">of trades followed the plan</p>
                  </div>
                  <div className="text-sm space-y-1">
                    <div className="flex justify-between">
                      <span>Total closed trades</span>
                      <span className="font-medium">{behavior.total_trades}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Exit Timing</CardTitle>
                </CardHeader>
                <CardContent>
                  {behaviorPie.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={behaviorPie}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value}`}
                        >
                          {behaviorPie.map((_, i) => (
                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                          ))}
                        </Pie>
                        <Legend />
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-muted-foreground text-center">
                      Add post-trade reviews with exit timing to see this chart.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <p className="text-muted-foreground text-center">
                  No behavioral data yet. Close trades and add post-reviews to see analysis.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
