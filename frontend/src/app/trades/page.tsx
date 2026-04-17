"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, Search } from "lucide-react";
import { api, type Trade } from "@/lib/api";

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filter, setFilter] = useState({ symbol: "", strategy: "", status: "" });
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrades();
  }, []);

  async function loadTrades() {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filter.symbol) params.symbol = filter.symbol;
      if (filter.strategy) params.strategy = filter.strategy;
      if (filter.status) params.status = filter.status;
      const data = await api.getTrades(params);
      setTrades(data);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const payload = {
      strategy_name: fd.get("strategy_name") as string,
      account: fd.get("account") as string,
      entry_timestamp: new Date().toISOString(),
      underlying_symbol: (fd.get("underlying_symbol") as string).toUpperCase(),
      entry_price: parseFloat(fd.get("entry_price") as string),
      position_type: fd.get("position_type") as string,
      direction: fd.get("direction") as string,
      quantity: parseInt(fd.get("quantity") as string),
      trade_thesis: fd.get("trade_thesis") as string,
      entry_rationale: fd.get("entry_rationale") as string,
      invalidation_conditions: fd.get("invalidation_conditions") as string,
      entry_iv: fd.get("entry_iv") ? parseFloat(fd.get("entry_iv") as string) : undefined,
      entry_delta: fd.get("entry_delta") ? parseFloat(fd.get("entry_delta") as string) : undefined,
      entry_theta: fd.get("entry_theta") ? parseFloat(fd.get("entry_theta") as string) : undefined,
      entry_vega: fd.get("entry_vega") ? parseFloat(fd.get("entry_vega") as string) : undefined,
      strike_price: fd.get("strike_price") ? parseFloat(fd.get("strike_price") as string) : undefined,
      premium: fd.get("premium") ? parseFloat(fd.get("premium") as string) : undefined,
      max_risk: fd.get("max_risk") ? parseFloat(fd.get("max_risk") as string) : undefined,
      max_profit: fd.get("max_profit") ? parseFloat(fd.get("max_profit") as string) : undefined,
    };
    await api.createTrade(payload);
    setShowNew(false);
    loadTrades();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Trade Journal</h2>
          <p className="text-muted-foreground">Record, review, and analyze every trade</p>
        </div>
        <Dialog open={showNew} onOpenChange={setShowNew}>
          <DialogTrigger render={<Button />}>
            <Plus className="h-4 w-4 mr-2" />New Trade
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Log New Trade</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Symbol *</label>
                  <Input name="underlying_symbol" required placeholder="TSLA" />
                </div>
                <div>
                  <label className="text-sm font-medium">Strategy *</label>
                  <Input name="strategy_name" required placeholder="covered_call" />
                </div>
                <div>
                  <label className="text-sm font-medium">Account *</label>
                  <Input name="account" required placeholder="Webull" />
                </div>
                <div>
                  <label className="text-sm font-medium">Entry Price *</label>
                  <Input name="entry_price" type="number" step="0.01" required />
                </div>
                <div>
                  <label className="text-sm font-medium">Position Type *</label>
                  <select name="position_type" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required>
                    <option value="stock">Stock</option>
                    <option value="option">Option</option>
                    <option value="spread">Spread</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Direction *</label>
                  <select name="direction" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required>
                    <option value="long">Long</option>
                    <option value="short">Short</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Quantity *</label>
                  <Input name="quantity" type="number" required />
                </div>
                <div>
                  <label className="text-sm font-medium">IV at Entry</label>
                  <Input name="entry_iv" type="number" step="0.01" />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium">Delta</label>
                  <Input name="entry_delta" type="number" step="0.01" />
                </div>
                <div>
                  <label className="text-sm font-medium">Theta</label>
                  <Input name="entry_theta" type="number" step="0.01" />
                </div>
                <div>
                  <label className="text-sm font-medium">Vega</label>
                  <Input name="entry_vega" type="number" step="0.01" />
                </div>
                <div>
                  <label className="text-sm font-medium">Strike</label>
                  <Input name="strike_price" type="number" step="0.01" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium">Premium</label>
                  <Input name="premium" type="number" step="0.01" />
                </div>
                <div>
                  <label className="text-sm font-medium">Max Risk</label>
                  <Input name="max_risk" type="number" step="0.01" />
                </div>
                <div>
                  <label className="text-sm font-medium">Max Profit</label>
                  <Input name="max_profit" type="number" step="0.01" />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Trade Thesis *</label>
                <Textarea name="trade_thesis" required placeholder="Why does this trade exist?" />
              </div>
              <div>
                <label className="text-sm font-medium">Entry Rationale *</label>
                <Textarea name="entry_rationale" required placeholder="Why now?" />
              </div>
              <div>
                <label className="text-sm font-medium">Invalidation Conditions *</label>
                <Textarea name="invalidation_conditions" required placeholder="What proves this trade wrong?" />
              </div>

              <Button type="submit" className="w-full">Log Trade</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="text-sm font-medium">Symbol</label>
              <Input
                placeholder="Filter by symbol..."
                value={filter.symbol}
                onChange={(e) => setFilter({ ...filter, symbol: e.target.value })}
              />
            </div>
            <div className="flex-1">
              <label className="text-sm font-medium">Strategy</label>
              <Input
                placeholder="Filter by strategy..."
                value={filter.strategy}
                onChange={(e) => setFilter({ ...filter, strategy: e.target.value })}
              />
            </div>
            <div className="w-32">
              <label className="text-sm font-medium">Status</label>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={filter.status}
                onChange={(e) => setFilter({ ...filter, status: e.target.value })}
              >
                <option value="">All</option>
                <option value="open">Open</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <Button onClick={loadTrades} variant="secondary">
              <Search className="h-4 w-4 mr-2" />Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Trade List */}
      <Card>
        <CardHeader>
          <CardTitle>Trades ({trades.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : trades.length === 0 ? (
            <p className="text-muted-foreground">No trades found. Log your first trade above.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 font-medium text-muted-foreground">Symbol</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Strategy</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Type</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Dir</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">Entry</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">Exit</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">P&L</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Status</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((t) => (
                    <tr key={t.id} className="border-b border-border last:border-0 hover:bg-accent/50">
                      <td className="py-3 font-medium">{t.underlying_symbol}</td>
                      <td className="py-3">{t.strategy_name}</td>
                      <td className="py-3"><Badge variant="outline">{t.position_type}</Badge></td>
                      <td className="py-3">
                        <Badge variant={t.direction === "long" ? "default" : "secondary"}>
                          {t.direction}
                        </Badge>
                      </td>
                      <td className="py-3 text-right font-mono">${t.entry_price.toFixed(2)}</td>
                      <td className="py-3 text-right font-mono">
                        {t.exit_price ? `$${t.exit_price.toFixed(2)}` : "---"}
                      </td>
                      <td className={`py-3 text-right font-mono font-medium ${
                        t.realized_pnl == null ? "" : t.realized_pnl >= 0 ? "text-green-500" : "text-red-500"
                      }`}>
                        {t.realized_pnl != null ? `$${t.realized_pnl.toFixed(2)}` : "---"}
                      </td>
                      <td className="py-3">
                        <Badge variant={t.status === "open" ? "default" : "secondary"}>
                          {t.status}
                        </Badge>
                      </td>
                      <td className="py-3 text-muted-foreground">
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
