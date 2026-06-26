import json
import urllib.request
import urllib.error
import time

BACKEND_URL = "http://localhost:8000"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = response.read().decode("utf-8")
            return response.status, json.loads(res_data)
    except urllib.error.HTTPError as e:
        res_data = e.read().decode("utf-8")
        try:
            parsed = json.loads(res_data)
        except Exception:
            parsed = res_data
        return e.code, parsed
    except Exception as e:
        return 0, str(e)

def run_e2e_test():
    print("=== STARTING END-TO-END LOAN LIFECYCLE TEST ===")
    
    # 1. Login as loan officer
    print("\n1. Logging in as admin (loan_officer)...")
    code, res = make_request(
        f"{BACKEND_URL}/api/auth/login/",
        method="POST",
        data={"username": "admin", "password": "admin1234"}
    )
    if code != 200:
        print(f"Login failed: {res}")
        return
    token = res.get("access")
    print(f"Logged in successfully! Token: {token[:15]}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get a client (VERIFIED)
    print("\n2. Fetching client list...")
    code, clients = make_request(f"{BACKEND_URL}/api/clients/", headers=headers)
    if code != 200 or not clients:
        print(f"Failed to fetch clients: {clients}")
        return
    
    client_list = clients.get("results", []) if isinstance(clients, dict) else clients
    if not client_list:
        print("No clients found in response.")
        return
        
    # Let's find a verified or active client
    client = None
    for c in client_list:
        if c.get("status") in ["VERIFIED", "ACTIVE"]:
            client = c
            break
    if not client:
        client = client_list[0]
        print(f"No VERIFIED client found. Using client {client.get('id')} ({client.get('status')})")
    else:
        print(f"Selected client: {client.get('first_name')} {client.get('last_name')} (ID: {client.get('id')}), Status: {client.get('status')}")

    # 3. Get products list
    print("\n3. Fetching loan products...")
    code, products = make_request(f"{BACKEND_URL}/api/loans/products/", headers=headers)
    if code != 200 or not products:
        print(f"Failed to fetch products: {products}")
        return
        
    product_list = products.get("results", []) if isinstance(products, dict) else products
    if not product_list:
        print("No loan products found.")
        return
    product = product_list[0]
    print(f"Selected product: {product.get('name')} (ID: {product.get('id')})")

    # 4. Create loan application
    print("\n4. Creating new loan application (DRAFT)...")
    app_payload = {
        "client": client.get("id"),
        "loan_product": product.get("id"),
        "requested_amount": 120000.0,
        "requested_duration_months": 12,
        "loan_purpose": "BUSINESS_EXPANSION",
        "purpose_description": "Expanding grocery store stock",
        "officer_notes": "Client has strong local reputation"
    }
    code, app = make_request(
        f"{BACKEND_URL}/api/loans/applications/",
        method="POST",
        data=app_payload,
        headers=headers
    )
    if code != 201:
        print(f"Failed to create loan application: {app}")
        return
    app_id = app.get("id")
    print(f"Application created successfully! ID: {app_id}, Number: {app.get('application_number')}, Status: {app.get('status')}")

    # 5. Add cashflow assessment
    print(f"\n5. Adding cashflow assessment to application {app_id}...")
    cashflow_payload = {
        "monthly_income": 95000.0,
        "other_income": 15000.0,
        "monthly_expenses": 40000.0,
        "existing_loan_payments": 5000.0,
        "proposed_monthly_payment": 10000.0,
        "officer_assessment_notes": "Very stable cashflow, high debt coverage"
    }
    code, cashflow = make_request(
        f"{BACKEND_URL}/api/loans/applications/{app_id}/cashflow/",
        method="POST",
        data=cashflow_payload,
        headers=headers
    )
    if code != 201:
        print(f"Failed to add cashflow: {cashflow}")
        return
    print(f"Cashflow assessment added successfully! Net cashflow: {cashflow.get('net_cashflow')}, DTI: {cashflow.get('debt_to_income_ratio')}")

    # 6. Submit application
    print(f"\n6. Submitting application {app_id}...")
    code, submit_res = make_request(
        f"{BACKEND_URL}/api/loans/applications/{app_id}/submit/",
        method="POST",
        headers=headers
    )
    if code != 200:
        print(f"Failed to submit application: {submit_res}")
        return
    print(f"Application submitted successfully! New Status: {submit_res.get('status') or 'AI_SCREENING'}")

    # 7. Trigger risk assessment (Calls A2 risk score agent)
    print(f"\n7. Triggering Risk Assessment (A2) for application {app_id}...")
    code, risk_res = make_request(
        f"{BACKEND_URL}/api/loans/applications/{app_id}/risk-assess/",
        method="POST",
        headers=headers
    )
    if code != 200:
        print(f"Failed to run risk assessment: {risk_res}")
        return
    print(f"Risk assessment completed! Risk Score: {risk_res.get('risk_score')}, Risk Category: {risk_res.get('risk_category')}")
    print(f"AI Rationale: {risk_res.get('agent_response', {}).get('rationale')}")

    # 8. Trigger recommendation (Calls A3 recommendation agent)
    print(f"\n8. Triggering AI Recommendation (A3) for application {app_id}...")
    code, rec_res = make_request(
        f"{BACKEND_URL}/api/loans/applications/{app_id}/recommend/",
        method="POST",
        headers=headers
    )
    if code != 200:
        print(f"Failed to run AI recommendation: {rec_res}")
        return
    print(f"AI Recommendation completed! Recommendation: {rec_res.get('recommendation')}")
    print(f"Explanation: {rec_res.get('explanation')}")
    
    print("\n=== E2E LOAN LIFECYCLE TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_e2e_test()
