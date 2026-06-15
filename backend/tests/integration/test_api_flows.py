import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass1",
            "full_name": "New User",
            "default_currency": "USD",
        },
    )
    assert register.status_code == 201
    data = register.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "newuser@example.com", "password": "securepass1"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


@pytest.mark.asyncio
async def test_wallet_deposit_withdraw_flow(client, auth_headers):
    headers, _ = auth_headers

    create = await client.post(
        "/api/v1/wallets",
        json={"currency": "USD"},
        headers=headers,
    )
    assert create.status_code == 201
    wallet_id = create.json()["id"]

    deposit = await client.post(
        f"/api/v1/wallets/{wallet_id}/deposit",
        json={"amount_minor_units": 25000},
        headers=headers,
    )
    assert deposit.status_code == 200
    assert deposit.json()["wallet"]["balance_minor_units"] == 25000

    withdraw = await client.post(
        f"/api/v1/wallets/{wallet_id}/withdraw",
        json={"amount_minor_units": 5000},
        headers=headers,
    )
    assert withdraw.status_code == 200
    assert withdraw.json()["wallet"]["balance_minor_units"] == 20000


@pytest.mark.asyncio
async def test_transaction_history(client, auth_headers):
    headers, _ = auth_headers

    create = await client.post("/api/v1/wallets", json={"currency": "EUR"}, headers=headers)
    wallet_id = create.json()["id"]
    await client.post(
        f"/api/v1/wallets/{wallet_id}/deposit",
        json={"amount_minor_units": 10000},
        headers=headers,
    )

    history = await client.get("/api/v1/transactions?page=1&page_size=10", headers=headers)
    assert history.status_code == 200
    data = history.json()
    assert data["total"] >= 1
    assert any(tx["type"] == "DEPOSIT" for tx in data["items"])


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code in (200, 503)
    assert "status" in response.json()
