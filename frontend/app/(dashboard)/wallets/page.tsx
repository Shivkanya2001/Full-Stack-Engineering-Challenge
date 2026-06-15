"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorAlert, LoadingSpinner } from "@/components/ui/Alert";
import { walletApi } from "@/services/endpoints";
import { ApiClientError } from "@/services/api-client";

const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"];

export default function WalletsPage() {
  const queryClient = useQueryClient();
  const [newCurrency, setNewCurrency] = useState("USD");
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);
  const [amount, setAmount] = useState("");

  const { data: wallets, isLoading } = useQuery({
    queryKey: ["wallets"],
    queryFn: walletApi.list,
  });

  const createMutation = useMutation({
    mutationFn: () => walletApi.create(newCurrency),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["wallets"] }),
  });

  const depositMutation = useMutation({
    mutationFn: ({ walletId, amount }: { walletId: string; amount: number }) =>
      walletApi.deposit(walletId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setAmount("");
    },
  });

  const withdrawMutation = useMutation({
    mutationFn: ({ walletId, amount }: { walletId: string; amount: number }) =>
      walletApi.withdraw(walletId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallets"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setAmount("");
    },
  });

  const error =
    (createMutation.error || depositMutation.error || withdrawMutation.error) instanceof ApiClientError
      ? (createMutation.error || depositMutation.error || withdrawMutation.error)?.message
      : null;

  if (isLoading) return <LoadingSpinner />;

  const toMinor = (val: string, currency: string) => {
    const num = parseFloat(val);
    if (isNaN(num)) return 0;
    return currency === "JPY" ? Math.round(num) : Math.round(num * 100);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Wallets</h1>
      {error && <ErrorAlert message={error} />}

      <Card title="Create wallet">
        <div className="flex flex-wrap gap-3">
          <select
            className="rounded-lg border border-border bg-card px-3 py-2"
            value={newCurrency}
            onChange={(e) => setNewCurrency(e.target.value)}
          >
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <Button onClick={() => createMutation.mutate()} loading={createMutation.isPending}>
            Create wallet
          </Button>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {wallets?.map((w) => (
          <Card key={w.id} title={`${w.currency} Wallet`}>
            <p className="mb-4 text-2xl font-bold text-primary">{w.balance_display}</p>
            <Button
              variant="secondary"
              className="mb-3 w-full"
              onClick={() => setSelectedWallet(selectedWallet === w.id ? null : w.id)}
            >
              {selectedWallet === w.id ? "Close" : "Deposit / Withdraw"}
            </Button>
            {selectedWallet === w.id && (
              <div className="space-y-3 border-t border-border pt-3">
                <Input
                  label={`Amount (${w.currency})`}
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    onClick={() =>
                      depositMutation.mutate({
                        walletId: w.id,
                        amount: toMinor(amount, w.currency),
                      })
                    }
                    loading={depositMutation.isPending}
                  >
                    Deposit
                  </Button>
                  <Button
                    variant="danger"
                    className="flex-1"
                    onClick={() =>
                      withdrawMutation.mutate({
                        walletId: w.id,
                        amount: toMinor(amount, w.currency),
                      })
                    }
                    loading={withdrawMutation.isPending}
                  >
                    Withdraw
                  </Button>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
