"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/ui/Alert";
import { transactionApi } from "@/services/endpoints";

const TX_TYPES = ["DEPOSIT", "WITHDRAWAL", "TRANSFER_OUT", "TRANSFER_IN", "CONVERSION_OUT", "CONVERSION_IN"];

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [type, setType] = useState("");
  const [currency, setCurrency] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const params: Record<string, string> = {
    page: String(page),
    page_size: "15",
  };
  if (type) params.type = type;
  if (currency) params.currency = currency;
  if (fromDate) params.from_date = new Date(fromDate).toISOString();
  if (toDate) params.to_date = new Date(toDate).toISOString();

  const { data, isLoading } = useQuery({
    queryKey: ["transactions", params],
    queryFn: () => transactionApi.list(params),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Transaction history</h1>

      <Card title="Filters">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <select
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm"
            value={type}
            onChange={(e) => { setType(e.target.value); setPage(1); }}
          >
            <option value="">All types</option>
            {TX_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm"
            placeholder="Currency (USD)"
            value={currency}
            onChange={(e) => { setCurrency(e.target.value.toUpperCase()); setPage(1); }}
          />
          <input
            type="date"
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm"
            value={fromDate}
            onChange={(e) => { setFromDate(e.target.value); setPage(1); }}
          />
          <input
            type="date"
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm"
            value={toDate}
            onChange={(e) => { setToDate(e.target.value); setPage(1); }}
          />
        </div>
      </Card>

      <Card>
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted">
                    <th className="pb-2 pr-4">Type</th>
                    <th className="pb-2 pr-4">Amount</th>
                    <th className="pb-2 pr-4">Currency</th>
                    <th className="pb-2 pr-4">Balance after</th>
                    <th className="pb-2">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((tx) => (
                    <tr key={tx.id} className="border-b border-border/50">
                      <td className="py-3 pr-4 font-medium">{tx.type}</td>
                      <td className="py-3 pr-4">{tx.amount_minor_units}</td>
                      <td className="py-3 pr-4">{tx.currency}</td>
                      <td className="py-3 pr-4">{tx.balance_after_minor_units}</td>
                      <td className="py-3 text-muted">
                        {new Date(tx.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!data?.items.length && (
                <p className="py-8 text-center text-muted">No transactions found.</p>
              )}
            </div>
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-muted">
                Page {data?.page} of {data?.total_pages || 1} ({data?.total} total)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  disabled={page >= (data?.total_pages || 1)}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
