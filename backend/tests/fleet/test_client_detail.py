"""Tests for fleet client detail endpoints."""


class TestClientDetail:
    def test_upsert_and_get_client_detail(self, http, db, admin_token):
        token, tenant_id, _ = admin_token

        # Create base client in clients module
        create_client = http.post(
            "/api/clients",
            json={"name": "Cliente PJ", "document": "12.345.678/0001-99", "type": "PJ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_client.status_code == 200
        client_id = create_client.json()["id"]

        payload = {
            "company_name": "Cliente PJ SA",
            "cnpj": "12.345.678/0001-99",
            "ie": "123456",
            "fleet_size_estimated": 14,
            "contract_type": "MENSAL",
            "contract_value": 25000.0,
            "payment_terms": "30 dias",
            "account_manager": "Joana",
        }

        upsert = http.put(
            f"/api/fleet/clients/{client_id}/detail",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert upsert.status_code == 200
        assert upsert.json()["company_name"] == "Cliente PJ SA"
        assert upsert.json()["fleet_size_estimated"] == 14

        get_detail = http.get(
            f"/api/fleet/clients/{client_id}/detail",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_detail.status_code == 200
        assert get_detail.json()["contract_type"] == "MENSAL"

    def test_get_client_detail_404(self, http, db, admin_token):
        token, _, _ = admin_token
        resp = http.get(
            "/api/fleet/clients/99999/detail",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
