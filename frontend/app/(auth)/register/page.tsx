"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorAlert } from "@/components/ui/Alert";
import { authApi } from "@/services/endpoints";
import { setToken, ApiClientError } from "@/services/api-client";

const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"];

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    default_currency: "USD",
  });

  const mutation = useMutation({
    mutationFn: () => authApi.register(form),
    onSuccess: (data) => {
      setToken(data.access_token);
      router.push("/dashboard");
    },
  });

  const error =
    mutation.error instanceof ApiClientError ? mutation.error.message : null;

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md" title="Create account">
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (form.password.length < 8) return;
            mutation.mutate();
          }}
        >
          {error && <ErrorAlert message={error} />}
          <Input
            label="Full name"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            required
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <Input
            label="Password"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            minLength={8}
            required
          />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-muted">Default currency</label>
            <select
              className="w-full rounded-lg border border-border bg-card px-3 py-2"
              value={form.default_currency}
              onChange={(e) => setForm({ ...form, default_currency: e.target.value })}
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" className="w-full" loading={mutation.isPending}>
            Register
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-muted">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}
