"use client";

import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/ui/Alert";
import { authApi, walletApi, transactionApi } from "@/services/endpoints";

export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
  });

  const { data: wallets, isLoading: walletsLoading } = useQuery({
    queryKey: ["wallets"],
    queryFn: walletApi.list,
  });

  const { data: transactions } = useQuery({
    queryKey: ["transactions", "recent"],
    queryFn: () => transactionApi.list({ page: "1", page_size: "5" }),
  });

  if (userLoading || walletsLoading) return <LoadingSpinner />;

  const totalWallets = wallets?.length ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Welcome, {user?.full_name}</h1>
        <p className="text-muted">Manage your multi-currency wallets</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card title="Wallets">
          <p className="text-3xl font-bold text-primary">{totalWallets}</p>
          <p className="text-sm text-muted">Active currency wallets</p>
        </Card>
        <Card title="Default currency">
          <p className="text-3xl font-bold">{user?.default_currency}</p>
        </Card>
        <Card title="Recent activity">
          <p className="text-3xl font-bold">{transactions?.total ?? 0}</p>
          <p className="text-sm text-muted">Total transactions</p>
        </Card>
      </div>

      <Card title="Wallet balances">
        <div className="grid gap-3 sm:grid-cols-2">
          {wallets?.map((w) => (
            <div key={w.id} className="rounded-lg border border-border p-4">
              <p className="text-sm text-muted">{w.currency}</p>
              <p className="text-xl font-semibold">{w.balance_display}</p>
            </div>
          ))}
          {wallets?.length === 0 && (
            <p className="text-muted">No wallets yet. Create one in the Wallets page.</p>
          )}
        </div>
      </Card>

      <Card title="Recent transactions">
        <div className="space-y-2">
          {transactions?.items.map((tx) => (
            <div key={tx.id} className="flex items-center justify-between border-b border-border py-2 text-sm">
              <span className="font-medium">{tx.type}</span>
              <span>{tx.amount_minor_units / 100} {tx.currency}</span>
              <span className="text-muted">{new Date(tx.created_at).toLocaleDateString()}</span>
            </div>
          ))}
          {!transactions?.items.length && <p className="text-muted">No transactions yet.</p>}
        </div>
      </Card>
    </div>
  );
}
