"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorAlert, LoadingSpinner } from "@/components/ui/Alert";
import { authApi } from "@/services/endpoints";
import { ApiClientError } from "@/services/api-client";

const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"];

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useQuery({ queryKey: ["me"], queryFn: authApi.me });
  const [fullName, setFullName] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [currency, setCurrency] = useState("USD");

  const mutation = useMutation({
    mutationFn: () =>
      authApi.updateProfile({
        full_name: fullName || undefined,
        profile_photo_url: photoUrl || undefined,
        default_currency: currency,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
  });

  useEffect(() => {
    if (user) {
      setFullName(user.full_name);
      setPhotoUrl(user.profile_photo_url || "");
      setCurrency(user.default_currency);
    }
  }, [user]);

  if (isLoading) return <LoadingSpinner />;

  const error = mutation.error instanceof ApiClientError ? mutation.error.message : null;

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">Profile</h1>
      <Card>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
        >
          {error && <ErrorAlert message={error} />}
          {mutation.isSuccess && (
            <p className="text-sm text-accent">Profile updated successfully.</p>
          )}
          <Input label="Email" value={user?.email || ""} disabled />
          <Input label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Input
            label="Profile photo URL"
            value={photoUrl}
            onChange={(e) => setPhotoUrl(e.target.value)}
            placeholder="https://..."
          />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-muted">Default currency</label>
            <select
              className="w-full rounded-lg border border-border bg-card px-3 py-2"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <Button type="submit" loading={mutation.isPending}>Save changes</Button>
        </form>
      </Card>
    </div>
  );
}
