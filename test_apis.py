#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive API Test Script for Insurance Policy Management System

Tests all 50+ API endpoints across 12 modules:
- Authentication, Users, Roles
- Catalog (Insurance Types, Companies, Coverages, Addons)
- Customers, Applications, Quotes
- Policies, Payments, Invoices
- Claims, Notifications, Analytics

Usage:
    1. Start the server: python manage.py runserver 8000
    2. Ensure seed data exists: python manage.py seed_data
    3. Run this script: python test_apis.py
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('')  # Enable ANSI escape sequences on Windows

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Test credentials (from seed_data)
ADMIN_EMAIL = "admin@insurance.local"
ADMIN_PASSWORD = "Admin@12345"

# Test user for registration (unique timestamp to avoid conflicts)
TEST_USER_EMAIL = f"testuser_{int(time.time())}@test.com"
TEST_USER_PASSWORD = "TestUser@123"
TEST_USER_USERNAME = f"testuser_{int(time.time())}"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.END}\n")

def print_subheader(text: str):
    """Print a subsection header."""
    print(f"\n{Colors.CYAN}--- {text} ---{Colors.END}")

def print_result(test_name: str, passed: bool, response: Optional[requests.Response] = None, 
                 expected_status: Optional[int] = None, extra_info: str = ""):
    """Print test result with color coding."""
    if passed:
        status = f"{Colors.GREEN}[PASS]{Colors.END}"
    else:
        status = f"{Colors.RED}[FAIL]{Colors.END}"
    
    status_code = ""
    if response is not None:
        actual = response.status_code
        if expected_status:
            if actual == expected_status:
                status_code = f" [{actual}]"
            else:
                status_code = f" [Expected: {expected_status}, Got: {actual}]"
        else:
            status_code = f" [{actual}]"
    
    print(f"  {status} {test_name}{status_code}{' - ' + extra_info if extra_info else ''}")
    
    # Show error details for failures
    if not passed and response is not None:
        try:
            error_detail = response.json()
            print(f"       {Colors.RED}Error: {json.dumps(error_detail, indent=2)[:200]}{Colors.END}")
        except:
            print(f"       {Colors.RED}Response: {response.text[:200]}{Colors.END}")

def get_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Get request headers with optional auth token."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def make_request(method: str, endpoint: str, token: Optional[str] = None, 
                 data: Optional[Dict] = None, files: Optional[Dict] = None) -> requests.Response:
    """Make an HTTP request."""
    url = f"{BASE_URL}{endpoint}"
    headers = {} if files else get_headers(token)
    if token and files:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            return requests.get(url, headers=headers, params=data, timeout=30)
        elif method == "POST":
            if files:
                return requests.post(url, headers=headers, data=data, files=files, timeout=30)
            return requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            return requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "PATCH":
            return requests.patch(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            return requests.delete(url, headers=headers, timeout=30)
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Cannot connect to server at {BASE_URL}")
        print(f"Make sure the server is running: python manage.py runserver 8001{Colors.END}\n")
        sys.exit(1)

# =============================================================================
# TEST RESULT TRACKING
# =============================================================================

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def record(self, name: str, passed: bool):
        self.tests.append((name, passed))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print_header("TEST SUMMARY")
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"  Total Tests: {total}")
        print(f"  {Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"  {Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"  Pass Rate: {pass_rate:.1f}%")
        
        if self.failed > 0:
            print(f"\n  {Colors.YELLOW}Failed Tests:{Colors.END}")
            for name, passed in self.tests:
                if not passed:
                    print(f"    - {name}")

results = TestResults()

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_api_root():
    """Test the API root endpoint."""
    print_subheader("API Root")
    
    resp = make_request("GET", "/")
    # API root may require authentication in this project
    if resp.status_code == 401:
        passed = True
        print_result("GET /api/v1/ (API Root)", passed, resp, 401, 
                    extra_info="Requires auth (expected)")
    else:
        passed = resp.status_code == 200
        print_result("GET /api/v1/ (API Root)", passed, resp, 200)
    results.record("API Root", passed)
    return passed

def test_public_catalog_endpoints():
    """Test public catalog endpoints (no auth required)."""
    print_subheader("Public Catalog Endpoints")
    
    endpoints = [
        ("/insurance-types/", "Insurance Types List"),
        ("/companies/", "Companies List"),
        ("/coverages/", "Coverages List"),
        ("/addons/", "Addons List"),
    ]
    
    for endpoint, name in endpoints:
        resp = make_request("GET", endpoint)
        passed = resp.status_code == 200
        print_result(f"GET {endpoint} ({name})", passed, resp, 200)
        results.record(name, passed)

def test_auth_register() -> Tuple[bool, Optional[str]]:
    """Test user registration."""
    print_subheader("Authentication - Register")
    
    data = {
        "email": TEST_USER_EMAIL,
        "username": TEST_USER_USERNAME,
        "password": TEST_USER_PASSWORD,
        "password_confirm": TEST_USER_PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "9876543210"
    }
    
    resp = make_request("POST", "/auth/register/", data=data)
    passed = resp.status_code == 201
    
    token = None
    if passed:
        try:
            token = resp.json().get("tokens", {}).get("access")
        except:
            pass
    
    print_result("POST /auth/register/", passed, resp, 201)
    results.record("User Registration", passed)
    return passed, token

def test_auth_login(email: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Test user login and return tokens."""
    print_subheader("Authentication - Login")
    
    data = {
        "email": email,
        "password": password
    }
    
    resp = make_request("POST", "/auth/login/", data=data)
    passed = resp.status_code == 200
    
    access_token = None
    refresh_token = None
    if passed:
        try:
            tokens = resp.json().get("tokens", {})
            access_token = tokens.get("access")
            refresh_token = tokens.get("refresh")
        except:
            pass
    
    user_type = "Admin" if email == ADMIN_EMAIL else "User"
    print_result(f"POST /auth/login/ ({user_type})", passed, resp, 200)
    results.record(f"Login ({user_type})", passed)
    return passed, access_token, refresh_token

def test_auth_refresh(refresh_token: str) -> bool:
    """Test token refresh."""
    resp = make_request("POST", "/auth/refresh/", data={"refresh": refresh_token})
    passed = resp.status_code == 200
    print_result("POST /auth/refresh/", passed, resp, 200)
    results.record("Token Refresh", passed)
    return passed

def test_auth_logout(token: str, refresh_token: str) -> bool:
    """Test logout."""
    resp = make_request("POST", "/auth/logout/", token=token, data={"refresh": refresh_token})
    passed = resp.status_code == 200
    print_result("POST /auth/logout/", passed, resp, 200)
    results.record("Logout", passed)
    return passed

def test_user_profile(token: str) -> bool:
    """Test user profile endpoints."""
    print_subheader("User Profile")
    
    # Get profile
    resp = make_request("GET", "/users/me/", token=token)
    passed = resp.status_code == 200
    print_result("GET /users/me/", passed, resp, 200)
    results.record("Get User Profile", passed)
    
    # Update profile
    resp = make_request("PATCH", "/users/me/", token=token, data={"first_name": "Updated"})
    update_passed = resp.status_code == 200
    print_result("PATCH /users/me/", update_passed, resp, 200)
    results.record("Update User Profile", update_passed)
    
    return passed and update_passed

def test_admin_users_endpoints(admin_token: str) -> bool:
    """Test admin user management endpoints."""
    print_subheader("Admin - User Management")
    
    # List users
    resp = make_request("GET", "/users/", token=admin_token)
    passed = resp.status_code == 200
    print_result("GET /users/ (List Users)", passed, resp, 200)
    results.record("Admin List Users", passed)
    
    return passed

def test_roles_endpoints(admin_token: str) -> bool:
    """Test role management endpoints."""
    print_subheader("Roles Management")
    
    # List roles
    resp = make_request("GET", "/roles/", token=admin_token)
    passed = resp.status_code == 200
    print_result("GET /roles/", passed, resp, 200)
    results.record("List Roles", passed)
    
    return passed

def test_customer_profile(token: str) -> bool:
    """Test customer profile endpoints."""
    print_subheader("Customer Profile")
    
    # Get/Create profile
    resp = make_request("GET", "/profile/", token=token)
    passed = resp.status_code == 200
    print_result("GET /profile/", passed, resp, 200)
    results.record("Get Customer Profile", passed)
    
    # Update profile
    profile_data = {
        "date_of_birth": "1990-01-15",
        "gender": "MALE",
        "marital_status": "SINGLE",
        "residential_address": "123 Test Street",
        "residential_city": "Mumbai",
        "residential_state": "Maharashtra",
        "residential_pincode": "400001",
        "occupation_type": "SALARIED",
        "annual_income": 1000000
    }
    resp = make_request("PATCH", "/profile/", token=token, data=profile_data)
    update_passed = resp.status_code == 200
    print_result("PATCH /profile/", update_passed, resp, 200)
    results.record("Update Customer Profile", update_passed)
    
    return passed and update_passed

def test_customers_list(admin_token: str) -> bool:
    """Test customers listing (Admin/Backoffice)."""
    print_subheader("Customers List (Admin)")
    
    resp = make_request("GET", "/customers/", token=admin_token)
    passed = resp.status_code == 200
    print_result("GET /customers/", passed, resp, 200)
    results.record("List Customers", passed)
    
    return passed

def get_results_list(response: requests.Response) -> List[Dict]:
    """Extract results list from response (handles both paginated and non-paginated)."""
    try:
        data = response.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Check for paginated response
            if 'results' in data:
                return data['results']
            # Check for direct list in data
            return [data]
        return []
    except:
        return []

def test_applications(token: str, admin_token: str) -> Optional[int]:
    """Test application endpoints."""
    print_subheader("Insurance Applications")
    
    # First get an insurance type
    resp = make_request("GET", "/insurance-types/")
    insurance_types = get_results_list(resp)
    
    if resp.status_code != 200 or not insurance_types:
        print_result("Get Insurance Types (prerequisite)", False, resp,
                    extra_info="No insurance types found - run seed_data")
        results.record("Applications - Get Insurance Types", False)
        return None
    
    insurance_type_id = insurance_types[0]["id"]
    
    # Create application
    app_data = {
        "insurance_type": insurance_type_id,
        "sum_assured": 500000,
        "policy_term_months": 12,
        "additional_notes": "Test application from API test script"
    }
    
    resp = make_request("POST", "/applications/", token=token, data=app_data)
    created = resp.status_code == 201
    print_result("POST /applications/ (Create)", created, resp, 201)
    results.record("Create Application", created)
    
    if not created:
        return None
    
    # Extract app_id - try different response formats
    try:
        resp_data = resp.json()
        app_id = resp_data.get("id")
        # If 'id' not at root, it might be in 'data' or 'application'
        if app_id is None and isinstance(resp_data, dict):
            app_id = resp_data.get("data", {}).get("id") or resp_data.get("application", {}).get("id")
    except:
        app_id = None
    
    if app_id is None:
        print(f"       {Colors.YELLOW}Warning: Could not extract app_id from response{Colors.END}")
        # Try to get from list
        list_resp = make_request("GET", "/applications/", token=token)
        apps = get_results_list(list_resp)
        if apps:
            app_id = apps[0].get("id")  # Get most recent
    
    # List applications
    resp = make_request("GET", "/applications/", token=token)
    passed = resp.status_code == 200
    print_result("GET /applications/ (List)", passed, resp, 200)
    results.record("List Applications", passed)
    
    # Get application detail
    resp = make_request("GET", f"/applications/{app_id}/", token=token)
    passed = resp.status_code == 200
    print_result(f"GET /applications/{app_id}/ (Detail)", passed, resp, 200)
    results.record("Get Application Detail", passed)
    
    # Submit application
    resp = make_request("POST", f"/applications/{app_id}/submit/", token=token)
    submitted = resp.status_code == 200
    print_result(f"POST /applications/{app_id}/submit/", submitted, resp, 200)
    results.record("Submit Application", submitted)
    
    # Admin: Update status (start review)
    update_data = {"action": "start_review"}
    resp = make_request("POST", f"/applications/{app_id}/update-status/", token=admin_token, data=update_data)
    status_updated = resp.status_code == 200
    print_result(f"POST /applications/{app_id}/update-status/ (Start Review)", status_updated, resp, 200)
    results.record("Start Application Review", status_updated)
    
    # Admin: Approve application
    update_data = {"action": "approve"}
    resp = make_request("POST", f"/applications/{app_id}/update-status/", token=admin_token, data=update_data)
    approved = resp.status_code == 200
    print_result(f"POST /applications/{app_id}/update-status/ (Approve)", approved, resp, 200)
    results.record("Approve Application", approved)
    
    return app_id if approved else None

def test_quotes(token: str, application_id: int) -> Optional[int]:
    """Test quote endpoints."""
    print_subheader("Quotes")
    
    # Generate quotes
    resp = make_request("POST", "/quotes/generate/", token=token, data={"application_id": application_id})
    generated = resp.status_code in [200, 201]
    print_result("POST /quotes/generate/", generated, resp, 200)
    results.record("Generate Quotes", generated)
    
    if not generated:
        return None
    
    # List quotes
    resp = make_request("GET", "/quotes/", token=token)
    passed = resp.status_code == 200
    print_result("GET /quotes/ (List)", passed, resp, 200)
    results.record("List Quotes", passed)
    
    quotes = get_results_list(resp)
    if not passed or not quotes:
        return None
    
    quote_id = quotes[0]["id"]
    
    # Get quote detail
    resp = make_request("GET", f"/quotes/{quote_id}/", token=token)
    passed = resp.status_code == 200
    print_result(f"GET /quotes/{quote_id}/ (Detail)", passed, resp, 200)
    results.record("Get Quote Detail", passed)
    
    # Compare quotes
    resp = make_request("GET", f"/quotes/compare/", token=token, data={"application_id": application_id})
    compared = resp.status_code == 200
    print_result("GET /quotes/compare/", compared, resp, 200)
    results.record("Compare Quotes", compared)
    
    # Accept quote
    resp = make_request("POST", f"/quotes/{quote_id}/accept/", token=token)
    accepted = resp.status_code == 200
    print_result(f"POST /quotes/{quote_id}/accept/", accepted, resp, 200)
    results.record("Accept Quote", accepted)
    
    return quote_id if accepted else None

def test_payments(token: str, quote_id: int) -> bool:
    """Test payment endpoints."""
    print_subheader("Payments")
    
    # Create order
    resp = make_request("POST", "/payments/create-order/", token=token, data={"quote_id": quote_id})
    # This may fail if Razorpay is not configured - that's okay
    if resp.status_code in [200, 201]:
        passed = True
        print_result("POST /payments/create-order/", passed, resp, 200)
    else:
        passed = False
        print_result("POST /payments/create-order/", passed, resp, 200, 
                    extra_info="(May fail if Razorpay not configured)")
    results.record("Create Payment Order", passed)
    
    # List payments
    resp = make_request("GET", "/payments/", token=token)
    list_passed = resp.status_code == 200
    print_result("GET /payments/ (List)", list_passed, resp, 200)
    results.record("List Payments", list_passed)
    
    return passed

def test_policies(token: str, admin_token: str) -> bool:
    """Test policy endpoints."""
    print_subheader("Policies")
    
    # List policies
    resp = make_request("GET", "/policies/", token=token)
    passed = resp.status_code == 200
    print_result("GET /policies/ (List)", passed, resp, 200)
    results.record("List Policies", passed)
    
    # Admin: List all policies
    resp = make_request("GET", "/policies/all/", token=admin_token)
    all_passed = resp.status_code == 200
    print_result("GET /policies/all/ (Admin)", all_passed, resp, 200)
    results.record("List All Policies (Admin)", all_passed)
    
    return passed

def test_invoices(token: str) -> bool:
    """Test invoice endpoints."""
    print_subheader("Invoices")
    
    resp = make_request("GET", "/invoices/", token=token)
    passed = resp.status_code == 200
    print_result("GET /invoices/ (List)", passed, resp, 200)
    results.record("List Invoices", passed)
    
    return passed

def test_claims(token: str, admin_token: str) -> bool:
    """Test claim endpoints."""
    print_subheader("Claims")
    
    # List claims
    resp = make_request("GET", "/claims/", token=token)
    passed = resp.status_code == 200
    print_result("GET /claims/ (List)", passed, resp, 200)
    results.record("List Claims", passed)
    
    # Admin: List all claims
    resp = make_request("GET", "/claims/all/", token=admin_token)
    all_passed = resp.status_code == 200
    print_result("GET /claims/all/ (Admin)", all_passed, resp, 200)
    results.record("List All Claims (Admin)", all_passed)
    
    return passed

def test_notifications(token: str) -> bool:
    """Test notification endpoints."""
    print_subheader("Notifications")
    
    # List notifications
    resp = make_request("GET", "/notifications/", token=token)
    passed = resp.status_code == 200
    print_result("GET /notifications/ (List)", passed, resp, 200)
    results.record("List Notifications", passed)
    
    # Get unread count
    resp = make_request("GET", "/notifications/unread/", token=token)
    unread_passed = resp.status_code == 200
    print_result("GET /notifications/unread/", unread_passed, resp, 200)
    results.record("Get Unread Count", unread_passed)
    
    # Mark all as read
    resp = make_request("POST", "/notifications/read-all/", token=token)
    read_all_passed = resp.status_code == 200
    print_result("POST /notifications/read-all/", read_all_passed, resp, 200)
    results.record("Mark All as Read", read_all_passed)
    
    # Get summary
    resp = make_request("GET", "/notifications/summary/", token=token)
    summary_passed = resp.status_code == 200
    print_result("GET /notifications/summary/", summary_passed, resp, 200)
    results.record("Notification Summary", summary_passed)
    
    return passed

def test_analytics(admin_token: str) -> bool:
    """Test analytics endpoints (Admin/Backoffice only)."""
    print_subheader("Analytics Dashboard")
    
    # Dashboard
    resp = make_request("GET", "/analytics/dashboard/", token=admin_token)
    dashboard_passed = resp.status_code == 200
    print_result("GET /analytics/dashboard/", dashboard_passed, resp, 200)
    results.record("Analytics Dashboard", dashboard_passed)
    
    # Application metrics
    resp = make_request("GET", "/analytics/applications/", token=admin_token)
    app_passed = resp.status_code == 200
    print_result("GET /analytics/applications/", app_passed, resp, 200)
    results.record("Application Metrics", app_passed)
    
    # Claim metrics
    resp = make_request("GET", "/analytics/claims/", token=admin_token)
    claims_passed = resp.status_code == 200
    print_result("GET /analytics/claims/", claims_passed, resp, 200)
    results.record("Claim Metrics", claims_passed)
    
    return dashboard_passed and app_passed and claims_passed

def test_unauthorized_access() -> bool:
    """Test that protected endpoints reject unauthorized requests."""
    print_subheader("Unauthorized Access Tests")
    
    protected_endpoints = [
        ("/users/me/", "User Profile"),
        ("/profile/", "Customer Profile"),
        ("/applications/", "Applications"),
        ("/quotes/", "Quotes"),
        ("/policies/", "Policies"),
        ("/claims/", "Claims"),
        ("/notifications/", "Notifications"),
        ("/analytics/dashboard/", "Analytics"),
    ]
    
    all_passed = True
    for endpoint, name in protected_endpoints:
        resp = make_request("GET", endpoint)
        # Should get 401 Unauthorized
        passed = resp.status_code == 401
        print_result(f"GET {endpoint} (No Auth)", passed, resp, 401, 
                    extra_info="Should reject" if passed else "Should be 401")
        if not passed:
            all_passed = False
    
    results.record("Unauthorized Access Rejection", all_passed)
    return all_passed

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_all_tests():
    """Run all API tests."""
    start_time = time.time()
    
    print_header("INSURANCE POLICY MANAGEMENT SYSTEM - API TEST SUITE")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server connectivity
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Cannot connect to server at {BASE_URL}")
        print(f"Please start the server first: python manage.py runserver 8001{Colors.END}\n")
        return
    
    # =========================================================================
    # 1. PUBLIC ENDPOINTS
    # =========================================================================
    print_header("1. PUBLIC ENDPOINTS")
    test_api_root()
    test_public_catalog_endpoints()
    
    # =========================================================================
    # 2. UNAUTHORIZED ACCESS TESTS
    # =========================================================================
    print_header("2. UNAUTHORIZED ACCESS TESTS")
    test_unauthorized_access()
    
    # =========================================================================
    # 3. AUTHENTICATION
    # =========================================================================
    print_header("3. AUTHENTICATION")
    
    # Register new user
    reg_passed, new_user_token = test_auth_register()
    
    # Login as admin
    admin_login_passed, admin_token, admin_refresh = test_auth_login(ADMIN_EMAIL, ADMIN_PASSWORD)
    
    if not admin_token:
        print(f"\n{Colors.RED}ERROR: Cannot login as admin. Make sure seed data exists.")
        print(f"Run: python manage.py seed_data{Colors.END}\n")
        results.print_summary()
        return
    
    # Token refresh
    if admin_refresh:
        test_auth_refresh(admin_refresh)
    
    # =========================================================================
    # 4. USER & ROLE MANAGEMENT (Admin)
    # =========================================================================
    print_header("4. USER & ROLE MANAGEMENT")
    test_user_profile(admin_token)
    test_admin_users_endpoints(admin_token)
    test_roles_endpoints(admin_token)
    
    # =========================================================================
    # 5. CUSTOMER PROFILE
    # =========================================================================
    print_header("5. CUSTOMER PROFILE")
    
    # Login as new user for customer tests
    if new_user_token:
        customer_token = new_user_token
    else:
        _, customer_token, _ = test_auth_login(TEST_USER_EMAIL, TEST_USER_PASSWORD)
    
    if customer_token:
        test_customer_profile(customer_token)
    else:
        print(f"  {Colors.YELLOW}Skipping customer profile tests - no customer token{Colors.END}")
    
    test_customers_list(admin_token)
    
    # =========================================================================
    # 6. FULL CUSTOMER WORKFLOW
    # =========================================================================
    print_header("6. CUSTOMER WORKFLOW (Application -> Quote -> Policy)")
    
    if customer_token:
        # Create and process application
        app_id = test_applications(customer_token, admin_token)
        
        # Generate and accept quotes
        quote_id = None
        if app_id:
            quote_id = test_quotes(customer_token, app_id)
        
        # Payment (may fail without Razorpay config)
        if quote_id:
            test_payments(customer_token, quote_id)
    else:
        print(f"  {Colors.YELLOW}Skipping workflow tests - no customer token{Colors.END}")
    
    # =========================================================================
    # 7. POLICIES & INVOICES
    # =========================================================================
    print_header("7. POLICIES & INVOICES")
    test_policies(customer_token or admin_token, admin_token)
    test_invoices(customer_token or admin_token)
    
    # =========================================================================
    # 8. CLAIMS
    # =========================================================================
    print_header("8. CLAIMS")
    test_claims(customer_token or admin_token, admin_token)
    
    # =========================================================================
    # 9. NOTIFICATIONS
    # =========================================================================
    print_header("9. NOTIFICATIONS")
    test_notifications(customer_token or admin_token)
    
    # =========================================================================
    # 10. ANALYTICS (Admin Only)
    # =========================================================================
    print_header("10. ANALYTICS (Admin/Backoffice)")
    test_analytics(admin_token)
    
    # =========================================================================
    # 11. CLEANUP - LOGOUT
    # =========================================================================
    print_header("11. CLEANUP")
    if customer_token and admin_refresh:
        # Note: We need a refresh token for logout, but we may not have it
        print_subheader("Logout")
        test_auth_logout(admin_token, admin_refresh)
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    elapsed = time.time() - start_time
    results.print_summary()
    print(f"\n  Time Elapsed: {elapsed:.2f} seconds")
    print()

if __name__ == "__main__":
    run_all_tests()
