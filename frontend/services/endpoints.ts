import { apiRequest } from "./api-client";
import type {
  AuthResponse,
  ExchangeRate,
  PaginatedResponse,
  Transaction,
  Transfer,
  User,
  Wallet,
} from "@/types/api";

export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    default_currency: string;
  }) => apiRequest<AuthResponse>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }),

  login: (data: { email: string; password: string }) =>
    apiRequest<AuthResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) }),

  me: () => apiRequest<User>("/api/v1/auth/me"),

  updateProfile: (data: Partial<{ full_name: string; profile_photo_url: string; default_currency: string }>) =>
    apiRequest<User>("/api/v1/auth/me", { method: "PATCH", body: JSON.stringify(data) }),
};

export const walletApi = {
  list: () => apiRequest<Wallet[]>("/api/v1/wallets"),
  create: (currency: string) =>
    apiRequest<Wallet>("/api/v1/wallets", { method: "POST", body: JSON.stringify({ currency }) }),
  deposit: (walletId: string, amount_minor_units: number) =>
    apiRequest<{ wallet: Wallet }>(`/api/v1/wallets/${walletId}/deposit`, {
      method: "POST",
      body: JSON.stringify({ amount_minor_units }),
    }),
  withdraw: (walletId: string, amount_minor_units: number) =>
    apiRequest<{ wallet: Wallet }>(`/api/v1/wallets/${walletId}/withdraw`, {
      method: "POST",
      body: JSON.stringify({ amount_minor_units }),
    }),
};

export const transferApi = {
  create: (data: {
    receiver_email: string;
    sender_wallet_id: string;
    amount_minor_units: number;
    receiver_currency?: string;
  }, idempotencyKey: string) =>
    apiRequest<Transfer>("/api/v1/transfers", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(data),
    }),
};

export const conversionApi = {
  convert: (data: {
    source_wallet_id: string;
    target_wallet_id: string;
    amount_minor_units: number;
  }) =>
    apiRequest<Record<string, unknown>>("/api/v1/conversions", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const exchangeApi = {
  latest: (base?: string) =>
    apiRequest<ExchangeRate[]>(`/api/v1/exchange-rates${base ? `?base_currency=${base}` : ""}`),
};

export const transactionApi = {
  list: (params: Record<string, string>) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest<PaginatedResponse<Transaction>>(`/api/v1/transactions?${query}`);
  },
};
