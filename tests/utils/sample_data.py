from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_fake_user(role_name: str = "LOGISTIC_MANAGER") -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        name="Test User",
        username="test.user",
        email="test.user@example.com",
        phone="9999999999",
        address="123 Test Street",
        role=SimpleNamespace(name=role_name),
        warehouse_id=None,
        is_active=True,
        approval_status="APPROVED",
        company_name=None,
        tax_id=None,
        contact_person=None,
        business_email=None,
        business_phone=None,
        created_at=now,
    )


def make_user_profile_dict(role_name: str = "INDIVIDUAL") -> dict[str, Any]:
    user = make_fake_user(role_name=role_name)
    return {
        "id": str(user.id),
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "role": role_name,
        "warehouse_id": None,
        "is_active": True,
        "approval_status": "APPROVED",
        "company_name": None,
        "tax_id": None,
        "contact_person": None,
        "business_email": None,
        "business_phone": None,
        "created_at": utc_now_iso(),
    }


def make_registration_response(
    pending_approval: bool = False,
    role_name: str = "INDIVIDUAL",
) -> dict[str, Any]:
    if pending_approval:
        return {
            "access_token": None,
            "refresh_token": None,
            "token_type": "bearer",
            "user": make_user_profile_dict(role_name=role_name),
            "pending_approval": True,
            "message": "Your account is pending approval",
        }
    return {
        "access_token": "access-token-123",
        "refresh_token": "refresh-token-123",
        "token_type": "bearer",
        "user": make_user_profile_dict(role_name=role_name),
        "pending_approval": False,
        "message": "Registration successful",
    }


def make_login_response(role_name: str = "INDIVIDUAL") -> dict[str, Any]:
    return {
        "access_token": "access-token-123",
        "refresh_token": "refresh-token-123",
        "token_type": "bearer",
        "user": make_user_profile_dict(role_name=role_name),
    }


def make_order_item() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "sku": "BOX-MEDIUM",
        "quantity": 3,
        "box_count": 2,
        "estimated_volume": 1.5,
    }


def make_order_response(
    status: str = "CONFIRMED",
    order_type: str = "MOVE",
) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "tracking_code": "TRK-1001",
        "order_type": order_type,
        "status": status,
        "warehouse_substatus": None,
        "picking_started_at": None,
        "picking_completed_at": None,
        "packing_started_at": None,
        "packing_completed_at": None,
        "customer_id": str(uuid4()),
        "warehouse_id": str(uuid4()),
        "assigned_driver_id": None,
        "assigned_vehicle_id": None,
        "assigned_driver_name": None,
        "assigned_vehicle_code": None,
        "pickup_addr": "123 Pickup Road",
        "delivery_addr": "456 Delivery Road",
        "cargo_type": "HOUSEHOLD",
        "vehicle_type": "TRUCK",
        "labor_count": 2,
        "base_amount": 1000.0,
        "vehicle_amount": 300.0,
        "labor_amount": 200.0,
        "materials_amount": 50.0,
        "packing_amount": 150.0,
        "platform_fee": 20.0,
        "tax_amount": 150.0,
        "total_amount": 1870.0,
        "payment_mode": "ONLINE",
        "payment_status": "pending",
        "paid_amount": 0.0,
        "declared_value": 0.0,
        "service_otp": None,
        "service_otp_sent_at": None,
        "service_otp_verified_at": None,
        "service_time_block": None,
        "scheduled_at": None,
        "cancel_reason": None,
        "cancellation_fee": 0.0,
        "wallet_refund_amount": 0.0,
        "delivered_at": None,
        "delivery_notes": None,
        "pod_photos": [],
        "pod_signature": None,
        "customer_name": "Jane Doe",
        "customer_phone": "9999999999",
        "created_at": utc_now_iso(),
        "items": [make_order_item()],
    }


def make_order_list_response(total: int = 1) -> dict[str, Any]:
    return {
        "items": [make_order_response()],
        "total": total,
        "page": 1,
        "page_size": 20,
    }


def make_tracking_item(status: str = "On-Duty") -> dict[str, Any]:
    return {
        "driver_id": str(uuid4()),
        "driver_name": "Driver One",
        "latitude": 19.076,
        "longitude": 72.8777,
        "vehicle_id": str(uuid4()),
        "vehicle_code": "VH-001",
        "status": status,
        "last_updated": utc_now_iso(),
    }
