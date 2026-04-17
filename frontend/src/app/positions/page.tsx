"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, TrendingUp, TrendingDown } from "lucide-react";
import { api, type Position } from "@/lib/api";

export default function PositionsPage() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [showNew, setShowNew] = useState(false);

  useEffect(() => {
    api.getPositions().then(setPositions).catch(() => {});
  }, []);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    await api.createPosition({
      symbol: (fd.get("symbol") as string).toUpperCase(),
      quantity: parseFloat(fd.get("quantity") as string),
      avg_cost: parseFloat(fd.get("avg_cost") as string),
      position_type: fd.get("position_type") as string,
      notes: fd.get("notes") as string || undefined,
    });
    setShowNew(false);
    api.getPositions().then(setPositions);
  }

  const totalValue = positions.reduce((s, p) => s + (p.current_value || 0), 0);
  const totalCost = positions.reduce((s, p) => s + p.avg_cost * p.quantity, 0);
  const totalPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Positions</h2>
          <p className="text-muted-foreground">Long-term core holdings and tactical positions</p>
        </div>
        <Dialog open={showNew} onOpenChange={setShowNew}>
          <DialogTrigger render={<Button />}>
            <Plus className="h-4 w-4 mr-2" />Add Position
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Position</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Symbol</label>
                  <Input name="symbol" required placeholder="TSLA" />
                </div>
                <div>
                  <label className="text-sm font-medium">Quantity</label>
                  <Input name="quantity" type="number" step="0.01" required />
                </div>
                <div>
                  <label className="text-sm font-medium">Avg Cost</label>
                  <Input name="avg_cost" type="number" step="0.01" required />
                </div>
                <div>
                  <label className="text-sm font-medium">Type</label>
                  <select name="position_type" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                    <option value="core_hold">Core Hold</option>
                    <option value="tactical">Tactical</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Notes</label>
                <Input name="notes" placeholder="Optional notes..." />
              </div>
              <Button type="submit" className="w-full">Add Position</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${totalValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Cost Basis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${totalCost.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Unrealized P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold flex items-center gap-2 ${totalPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
              {totalPnl >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
              ${Math.abs(totalPnl).toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Positions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          {positions.length === 0 ? (
            <p className="text-muted-foreground">No positions yet. Add your core holdings above.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 font-medium text-muted-foreground">Symbol</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Type</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">Qty</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">Avg Cost</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">Value</th>
                    <th className="text-right py-2 font-medium text-muted-foreground">P&L</th>
                    <th className="text-left py-2 font-medium text-muted-foreground">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((p) => (
                    <tr key={p.id} className="border-b border-border last:border-0">
                      <td className="py-3 font-bold text-lg">{p.symbol}</td>
                      <td className="py-3">
                        <Badge variant={p.position_type === "core_hold" ? "default" : "secondary"}>
                          {p.position_type === "core_hold" ? "Core" : "Tactical"}
                        </Badge>
                      </td>
                      <td className="py-3 text-right font-mono">{p.quantity}</td>
                      <td className="py-3 text-right font-mono">${p.avg_cost.toFixed(2)}</td>
                      <td className="py-3 text-right font-mono">
                        {p.current_value ? `$${p.current_value.toFixed(2)}` : "---"}
                      </td>
                      <td className={`py-3 text-right font-mono font-medium ${
                        p.unrealized_pnl == null ? "" : p.unrealized_pnl >= 0 ? "text-green-500" : "text-red-500"
                      }`}>
                        {p.unrealized_pnl != null ? `$${p.unrealized_pnl.toFixed(2)}` : "---"}
                      </td>
                      <td className="py-3 text-muted-foreground">{p.notes || ""}</td>
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
