"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorAlert, LoadingSpinner } from "@/components/ui/Alert";
import { transferApi, walletApi } from "@/services/endpoints";
import { ApiClientError } from "@/services/api-client";

export default function TransfersPage() {
  const queryClient = useQueryClient();
  const [receiverEmail, setReceiverEmail] = useState("");
  const [walletId, setWalletId] = useState("");
  const [amount, setAmount] = useState("");
  const [receiverCurrency, setReceiverCurrency] = useState("");

  const { data: wallets, isLoading } = useQuery({
    queryKey: ["wallets"],
    queryFn: walletApi.list,
  });

  const mutation = useMutation({
    mutationFn: () => {
      const wallet = wallets?.find((w) => w.id === walletId);
      const minor = wallet?.currency === "JPY"
        ? Math.round(parseFloat(amount))
        : Math.round(parseFloat(amount) * 100);
      return transferApi.create(
        {
          receiver_email: receiverEmail,
          sender_wallet_id: walletId,
          amount_minor_units: minor,
          receiver_currency: receiverCurrency || undefined,
        },
        crypto.randomUUID()
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setAmount("");
      setReceiverEmail("");
    },
  });

  const error = mutation.error instanceof ApiClientError ? mutation.error.message : null;
  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">Transfer funds</h1>
      {error && <ErrorAlert message={error} />}
      <Card>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          <Input
            label="Receiver email"
            type="email"
            value={receiverEmail}
            onChange={(e) => setReceiverEmail(e.target.value)}
            required
          />
          <div className="space-y-1">
            <label className="text-sm text-muted">From wallet</label>
            <select
              className="w-full rounded-lg border border-border bg-card px-3 py-2"
              value={walletId}
              onChange={(e) => setWalletId(e.target.value)}
              required
            >
              <option value="">Select wallet</option>
              {wallets?.map((w) => (
                <option key={w.id} value={w.id}>{w.currency} — {w.balance_display}</option>
              ))}
            </select>
          </div>
          <Input
            label="Receiver currency (optional, for cross-currency)"
            value={receiverCurrency}
            onChange={(e) => setReceiverCurrency(e.target.value.toUpperCase())}
            placeholder="e.g. EUR"
            maxLength={3}
          />
          <Input
            label="Amount"
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
          <Button type="submit" className="w-full" loading={mutation.isPending}>
            Send transfer
          </Button>
        </form>
        {mutation.isSuccess && mutation.data && (
          <div className="mt-4 rounded-lg border border-accent/30 bg-accent/10 p-3 text-sm">
            <p>Transfer completed: {mutation.data.sender_amount_display} → {mutation.data.receiver_amount_display}</p>
            <p className="text-muted">Status: {mutation.data.status}</p>
          </div>
        )}
      </Card>
    </div>
  );
}
