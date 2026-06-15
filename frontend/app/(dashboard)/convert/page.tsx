"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorAlert, LoadingSpinner } from "@/components/ui/Alert";
import { conversionApi, exchangeApi, walletApi } from "@/services/endpoints";
import { ApiClientError } from "@/services/api-client";

export default function ConvertPage() {
  const queryClient = useQueryClient();
  const [sourceId, setSourceId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [amount, setAmount] = useState("");

  const { data: wallets, isLoading } = useQuery({
    queryKey: ["wallets"],
    queryFn: walletApi.list,
  });

  const sourceWallet = wallets?.find((w) => w.id === sourceId);
  const { data: rates } = useQuery({
    queryKey: ["rates", sourceWallet?.currency],
    queryFn: () => exchangeApi.latest(sourceWallet?.currency),
    enabled: !!sourceWallet,
  });

  const mutation = useMutation({
    mutationFn: () => {
      const minor = sourceWallet?.currency === "JPY"
        ? Math.round(parseFloat(amount))
        : Math.round(parseFloat(amount) * 100);
      return conversionApi.convert({
        source_wallet_id: sourceId,
        target_wallet_id: targetId,
        amount_minor_units: minor,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setAmount("");
    },
  });

  const error = mutation.error instanceof ApiClientError ? mutation.error.message : null;
  if (isLoading) return <LoadingSpinner />;

  const targetWallet = wallets?.find((w) => w.id === targetId);
  const rate = rates?.find((r) => r.target_currency === targetWallet?.currency);

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">Convert currency</h1>
      {error && <ErrorAlert message={error} />}
      <Card>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <div className="space-y-1">
            <label className="text-sm text-muted">From wallet</label>
            <select
              className="w-full rounded-lg border border-border bg-card px-3 py-2"
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              required
            >
              <option value="">Select source</option>
              {wallets?.map((w) => (
                <option key={w.id} value={w.id}>{w.currency} — {w.balance_display}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-sm text-muted">To wallet</label>
            <select
              className="w-full rounded-lg border border-border bg-card px-3 py-2"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              required
            >
              <option value="">Select target</option>
              {wallets?.filter((w) => w.id !== sourceId).map((w) => (
                <option key={w.id} value={w.id}>{w.currency} — {w.balance_display}</option>
              ))}
            </select>
          </div>
          {rate && (
            <p className="text-sm text-muted">
              Rate: 1 {rate.base_currency} = {rate.rate} {rate.target_currency} ({rate.provider})
            </p>
          )}
          <Input
            label="Amount"
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
          <Button type="submit" className="w-full" loading={mutation.isPending}>
            Convert
          </Button>
        </form>
        {mutation.isSuccess && (
          <p className="mt-4 text-sm text-accent">Conversion completed successfully.</p>
        )}
      </Card>
    </div>
  );
}
