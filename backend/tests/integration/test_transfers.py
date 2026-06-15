import pytest


@pytest.mark.asyncio
async def test_transfer_between_users_api(client):
    sender_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "api-sender@example.com",
            "password": "password123",
            "full_name": "API Sender",
            "default_currency": "USD",
        },
    )
    sender_token = sender_reg.json()["access_token"]
    sender_headers = {"Authorization": f"Bearer {sender_token}"}

    receiver_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "api-receiver@example.com",
            "password": "password123",
            "full_name": "API Receiver",
            "default_currency": "USD",
        },
    )

    sender_wallet = await client.post(
        "/api/v1/wallets", json={"currency": "USD"}, headers=sender_headers
    )
    wallet_id = sender_wallet.json()["id"]

    await client.post(
        "/api/v1/wallets",
        json={"currency": "USD"},
        headers={"Authorization": f"Bearer {receiver_reg.json()['access_token']}"},
    )

    await client.post(
        f"/api/v1/wallets/{wallet_id}/deposit",
        json={"amount_minor_units": 50000},
        headers=sender_headers,
    )

    transfer = await client.post(
        "/api/v1/transfers",
        json={
            "receiver_email": "api-receiver@example.com",
            "sender_wallet_id": wallet_id,
            "amount_minor_units": 15000,
        },
        headers={**sender_headers, "Idempotency-Key": "api-transfer-key-1"},
    )
    assert transfer.status_code == 201
    data = transfer.json()
    assert data["sender_amount_minor_units"] == 15000
    assert data["receiver_amount_minor_units"] == 15000
