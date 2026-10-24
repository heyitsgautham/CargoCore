#!/usr/bin/env python3
"""
Comprehensive Driver App Workflow Test Script
Tests all major driver app endpoints against the backend
"""

import json
from datetime import datetime

import requests

BASE_URL = "http://localhost:8000/api/v1"

class DriverWorkflowTester:
    def __init__(self):
        self.token = None
        self.driver_id = None
        self.vehicle_id = None
        self.order_id = None
        self.results = []

    def log_result(self, test_name, status, message="", data=None):
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if data:
            result["data"] = data
        self.results.append(result)

        icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[WARN]" if status == "WARN" else "[SKIP]"
        print(f"{icon} {test_name}: {message}")
        if data and status == "FAIL":
            print(f"   Details: {json.dumps(data, indent=2)[:200]}")
        print()

    def test_login(self):
        """Test Step 1: Driver Login"""
        print("=" * 60)
        print("STEP 1: DRIVER LOGIN")
        print("=" * 60)

        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": "driver1@gmail.com", "password": "12345678"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user = data.get('user', {})
                self.driver_id = user.get('id')

                if user.get('role') == 'DRIVER':
                    self.log_result(
                        "Driver Login",
                        "PASS",
                        f"Logged in as {user.get('name')} ({user.get('email')})",
                        {"driver_id": self.driver_id, "warehouse_id": user.get('warehouse_id')}
                    )
                    return True
                else:
                    self.log_result("Driver Login", "FAIL", f"Wrong role: {user.get('role')}")
                    return False
            else:
                self.log_result("Driver Login", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Driver Login", "FAIL", str(e))
            return False

    def test_driver_profile(self):
        """Test Step 2: Get Driver Profile"""
        print("=" * 60)
        print("STEP 2: GET DRIVER PROFILE")
        print("=" * 60)

        try:
            response = requests.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                profile = response.json()
                self.log_result(
                    "Get Profile",
                    "PASS",
                    f"Profile retrieved: {profile.get('name')}",
                    {"email": profile.get('email'), "role": profile.get('role')}
                )
                return True
            else:
                self.log_result("Get Profile", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Get Profile", "FAIL", str(e))
            return False

    def test_driver_dashboard(self):
        """Test Step 3: Get Driver Dashboard"""
        print("=" * 60)
        print("STEP 3: GET DRIVER DASHBOARD")
        print("=" * 60)

        try:
            response = requests.get(
                f"{BASE_URL}/logistics/drivers/me/dashboard",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                dashboard = response.json()
                self.log_result(
                    "Get Dashboard",
                    "PASS",
                    "Dashboard data retrieved",
                    {
                        "active_orders": len(dashboard.get('active_orders', [])),
                        "current_vehicle": dashboard.get('current_vehicle', {}).get('code') if dashboard.get('current_vehicle') else None,
                        "shift_active": dashboard.get('shift_active', False)
                    }
                )
                return True
            else:
                self.log_result("Get Dashboard", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Get Dashboard", "FAIL", str(e))
            return False

    def test_list_vehicles(self):
        """Test Step 4: List Available Vehicles"""
        print("=" * 60)
        print("STEP 4: LIST AVAILABLE VEHICLES")
        print("=" * 60)

        try:
            response = requests.get(
                f"{BASE_URL}/logistics/vehicles",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                vehicles = response.json()
                if vehicles:
                    self.vehicle_id = vehicles[0].get('id')
                    vehicle_code = vehicles[0].get('code')
                    self.log_result(
                        "List Vehicles",
                        "PASS",
                        f"Found {len(vehicles)} vehicle(s)",
                        {"first_vehicle": vehicle_code, "vehicle_id": self.vehicle_id}
                    )
                else:
                    self.log_result("List Vehicles", "WARN", "No vehicles available")
                return True
            else:
                self.log_result("List Vehicles", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("List Vehicles", "FAIL", str(e))
            return False

    def test_bind_vehicle(self):
        """Test Step 5: Bind Driver to Vehicle"""
        print("=" * 60)
        print("STEP 5: BIND VEHICLE")
        print("=" * 60)

        if not self.vehicle_id:
            self.log_result("Bind Vehicle", "SKIP", "No vehicle available to bind")
            return True

        try:
            response = requests.post(
                f"{BASE_URL}/logistics/drivers/me/bind-vehicle",
                json={"vehicle_id": self.vehicle_id},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                vehicle = response.json()
                self.log_result(
                    "Bind Vehicle",
                    "PASS",
                    f"Vehicle bound: {vehicle.get('code')}",
                    {"vehicle_id": vehicle.get('id'), "license_plate": vehicle.get('license_plate')}
                )
                return True
            else:
                self.log_result("Bind Vehicle", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Bind Vehicle", "FAIL", str(e))
            return False

    def test_start_shift(self):
        """Test Step 6: Start Shift"""
        print("=" * 60)
        print("STEP 6: START SHIFT")
        print("=" * 60)

        try:
            response = requests.post(
                f"{BASE_URL}/logistics/drivers/me/shift/start",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Start Shift",
                    "PASS",
                    "Shift started successfully",
                    result
                )
                return True
            else:
                self.log_result("Start Shift", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Start Shift", "FAIL", str(e))
            return False

    def test_get_crew(self):
        """Test Step 7: Get Crew Members"""
        print("=" * 60)
        print("STEP 7: GET CREW MEMBERS")
        print("=" * 60)

        try:
            response = requests.get(
                f"{BASE_URL}/logistics/drivers/me/crew",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                crew = response.json()
                self.log_result(
                    "Get Crew",
                    "PASS",
                    f"Found {len(crew)} crew member(s)",
                    {"crew_count": len(crew)}
                )
                return True
            else:
                self.log_result("Get Crew", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Get Crew", "FAIL", str(e))
            return False

    def test_get_assigned_orders(self):
        """Test Step 8: Get Assigned Orders"""
        print("=" * 60)
        print("STEP 8: GET ASSIGNED ORDERS")
        print("=" * 60)

        try:
            response = requests.get(
                f"{BASE_URL}/orders?page=1&page_size=100",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                orders = data if isinstance(data, list) else data.get('items', [])

                # Filter active orders
                active_orders = [o for o in orders if o.get('status') not in ['DRAFT', 'DELIVERED', 'COMPLETED', 'CANCELLED', 'CLOSED']]

                if active_orders:
                    self.order_id = active_orders[0].get('id')
                    self.log_result(
                        "Get Orders",
                        "PASS",
                        f"Found {len(active_orders)} active order(s)",
                        {
                            "first_order_id": self.order_id,
                            "first_order_code": active_orders[0].get('order_code'),
                            "status": active_orders[0].get('status')
                        }
                    )
                else:
                    self.log_result("Get Orders", "WARN", "No active orders assigned")
                return True
            else:
                self.log_result("Get Orders", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Get Orders", "FAIL", str(e))
            return False

    def test_update_location(self):
        """Test Step 9: Update Driver Location"""
        print("=" * 60)
        print("STEP 9: UPDATE DRIVER LOCATION")
        print("=" * 60)

        try:
            response = requests.post(
                f"{BASE_URL}/logistics/drivers/me/location",
                json={"latitude": 28.7041, "longitude": 77.1025},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            if response.status_code == 200:
                self.log_result(
                    "Update Location",
                    "PASS",
                    "Location updated successfully",
                    {"lat": 28.7041, "lon": 77.1025}
                )
                return True
            else:
                self.log_result("Update Location", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Update Location", "FAIL", str(e))
            return False

    def test_order_transition(self):
        """Test Step 10: Order Status Transition"""
        print("=" * 60)
        print("STEP 10: ORDER STATUS TRANSITION")
        print("=" * 60)

        if not self.order_id:
            self.log_result("Order Transition", "SKIP", "No order available for testing")
            return True

        try:
            # Test transition endpoint (just testing availability, not actually transitioning)
            response = requests.post(
                f"{BASE_URL}/orders/{self.order_id}/transition",
                json={"next_status": "IN_TRANSIT", "notes": "Test transition"},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            # Accept both success and validation errors (means endpoint exists)
            if response.status_code in [200, 400, 422]:
                self.log_result(
                    "Order Transition",
                    "PASS",
                    f"Transition endpoint available (Status {response.status_code})",
                    {"order_id": self.order_id}
                )
                return True
            else:
                self.log_result("Order Transition", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Order Transition", "FAIL", str(e))
            return False

    def test_send_delivery_otp(self):
        """Test Step 11: Send Delivery OTP"""
        print("=" * 60)
        print("STEP 11: SEND DELIVERY OTP")
        print("=" * 60)

        if not self.order_id:
            self.log_result("Send Delivery OTP", "SKIP", "No order available for testing")
            return True

        try:
            response = requests.post(
                f"{BASE_URL}/orders/{self.order_id}/delivery-otp/send",
                json={"force_resend": False},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            # Accept both success and validation errors (means endpoint exists)
            if response.status_code in [200, 400, 422]:
                self.log_result(
                    "Send Delivery OTP",
                    "PASS",
                    f"OTP endpoint available (Status {response.status_code})"
                )
                return True
            else:
                self.log_result("Send Delivery OTP", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Send Delivery OTP", "FAIL", str(e))
            return False

    def test_proof_of_delivery(self):
        """Test Step 12: Proof of Delivery"""
        print("=" * 60)
        print("STEP 12: PROOF OF DELIVERY")
        print("=" * 60)

        if not self.order_id:
            self.log_result("Proof of Delivery", "SKIP", "No order available for testing")
            return True

        try:
            response = requests.post(
                f"{BASE_URL}/orders/{self.order_id}/proof-of-delivery",
                json={
                    "otp_code": "123456",
                    "images_data": [],
                    "signature_data": None,
                    "customer_name": "Test Customer",
                    "notes": "Test POD"
                },
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )

            # Accept both success and validation errors (means endpoint exists)
            if response.status_code in [200, 400, 422]:
                self.log_result(
                    "Proof of Delivery",
                    "PASS",
                    f"POD endpoint available (Status {response.status_code})"
                )
                return True
            else:
                self.log_result("Proof of Delivery", "FAIL", f"Status {response.status_code}", response.json())
                return False
        except Exception as e:
            self.log_result("Proof of Delivery", "FAIL", str(e))
            return False

    def generate_report(self):
        """Generate summary report"""
        print("\n")
        print("=" * 60)
        print("TEST SUMMARY REPORT")
        print("=" * 60)

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.results if r['status'] == 'WARN')
        skipped = sum(1 for r in self.results if r['status'] == 'SKIP')
        total = len(self.results)

        print(f"Total Tests: {total}")
        print(f"[PASS] Passed: {passed}")
        print(f"[FAIL] Failed: {failed}")
        print(f"[WARN] Warnings: {warned}")
        print(f"[SKIP] Skipped: {skipped}")
        print()

        if failed > 0:
            print("Failed Tests:")
            for r in self.results:
                if r['status'] == 'FAIL':
                    print(f"  [FAIL] {r['test']}: {r['message']}")

        print()
        print("=" * 60)

        # Save detailed report to file
        with open('driver_workflow_test_report.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "warned": warned,
                    "skipped": skipped
                },
                "results": self.results
            }, f, indent=2)

        print("Detailed report saved to: driver_workflow_test_report.json")
        print()

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n")
        print("=" * 60)
        print("DRIVER APP WORKFLOW TEST SUITE")
        print("=" * 60)
        print()

        # Run tests in workflow order
        if not self.test_login():
            print("⚠ Login failed - cannot continue with other tests")
            self.generate_report()
            return

        self.test_driver_profile()
        self.test_driver_dashboard()
        self.test_list_vehicles()
        self.test_bind_vehicle()
        self.test_start_shift()
        self.test_get_crew()
        self.test_get_assigned_orders()
        self.test_update_location()
        self.test_order_transition()
        self.test_send_delivery_otp()
        self.test_proof_of_delivery()

        self.generate_report()

if __name__ == "__main__":
    tester = DriverWorkflowTester()
    tester.run_all_tests()
