export interface User {
  id: string;
  email: string;
  full_name: string;
  profile_photo_url: string | null;
  default_currency: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Wallet {
  id: string;
  user_id: string;
  currency: string;
  balance_minor_units: number;
  balance_display: string;
  version: number;
  created_at: string;
}

export interface Transaction {
  id: string;
  wallet_id: string;
  type: string;
  amount_minor_units: number;
  currency: string;
  balance_after_minor_units: number;
  transfer_id: string | null;
  exchange_rate_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface Transfer {
  id: string;
  sender_user_id: string;
  receiver_user_id: string;
  sender_wallet_id: string;
  receiver_wallet_id: string;
  sender_amount_minor_units: number;
  receiver_amount_minor_units: number;
  sender_currency: string;
  receiver_currency: string;
  sender_amount_display: string;
  receiver_amount_display: string;
  exchange_rate_id: string | null;
  status: string;
  idempotency_key: string;
  created_at: string;
}

export interface ExchangeRate {
  id: string;
  base_currency: string;
  target_currency: string;
  rate: string;
  provider: string;
  fetched_at: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages?: number;
}
