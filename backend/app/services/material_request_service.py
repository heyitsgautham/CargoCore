"""Material requests: a warehouse manager asks for a new packing material and the logistics manager prices it.

Approval adds the material to rates_config.json and to the stock of every active hub.
"""

import json
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import (
    InventoryItem,
    MaterialRequest,
)
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.inventory import (
    MaterialRequestApprove,
    MaterialRequestCreate,
    MaterialRequestListResponse,
    MaterialRequestReject,
    MaterialRequestResponse,
)

MOVEMENT_TYPES = {"INBOUND", "OUTBOUND", "ADJUSTMENT", "ISSUE", "RESTOCK", "RESERVED", "PICK"}


# ─────────────────────────────────────────────────────────────────────────────
# Material Request Functions (WM requests new packing material -> LM approves)
# ─────────────────────────────────────────────────────────────────────────────


_RATES_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "rates_config.json"


def _to_material_request_response(req: MaterialRequest, requester: User | None = None, approver: User | None = None) -> MaterialRequestResponse:
    return MaterialRequestResponse(
        id=req.id,
        material_name=req.material_name,
        category=req.category,
        unit=req.unit,
        suggested_rate=req.suggested_rate,
        reason=req.reason,
        status=req.status,
        requested_by=req.requested_by,
        requested_by_name=getattr(requester, "full_name", None) or getattr(requester, "email", None) if requester else None,
        approved_by=req.approved_by,
        approved_by_name=getattr(approver, "full_name", None) or getattr(approver, "email", None) if approver else None,
        approved_rate=req.approved_rate,
        manager_notes=req.manager_notes,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


async def create_material_request(
    db: AsyncSession, data: MaterialRequestCreate, user: User
) -> MaterialRequestResponse:
    """WM creates a request for a new packing material."""
    req = MaterialRequest(
        material_name=data.material_name,
        category=data.category,
        unit=data.unit,
        suggested_rate=data.suggested_rate,
        reason=data.reason,
        status="PENDING",
        requested_by=user.id,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return _to_material_request_response(req, user)


async def list_material_requests(
    db: AsyncSession, status_filter: str | None, user: User
) -> MaterialRequestListResponse:
    """List material requests. LM sees all, WM sees only their own."""
    query = select(MaterialRequest)
    
    # WM only sees their own requests
    if user.role == "WAREHOUSE_MANAGER":
        query = query.where(MaterialRequest.requested_by == user.id)
    
    if status_filter:
        query = query.where(MaterialRequest.status == status_filter.upper())
    
    query = query.order_by(MaterialRequest.created_at.desc())
    result = await db.execute(query)
    requests = result.scalars().all()
    
    # Fetch user names
    items = []
    for req in requests:
        requester = None
        approver = None
        if req.requested_by:
            user_result = await db.execute(select(User).where(User.id == req.requested_by))
            requester = user_result.scalar_one_or_none()
        if req.approved_by:
            user_result = await db.execute(select(User).where(User.id == req.approved_by))
            approver = user_result.scalar_one_or_none()
        items.append(_to_material_request_response(req, requester, approver))
    
    return MaterialRequestListResponse(items=items, total=len(items))


async def _get_material_request(db: AsyncSession, request_id: UUID) -> MaterialRequest:
    result = await db.execute(select(MaterialRequest).where(MaterialRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material request not found")
    return req


def _material_sku(material_name: str) -> str:
    """Generate a stable inventory SKU from a material name. e.g. 'Bubble Wrap' → 'PKG-BUBBLE-WRAP'"""
    return "PKG-" + material_name.upper().replace(" ", "-")


async def sync_packing_materials_to_inventory(
    db: AsyncSession,
    materials: list[dict],
) -> None:
    """
    Upsert inventory items for every packing material in all active warehouses.
    - Creates the item if it doesn't exist (quantity_on_hand = 0, safety_stock = 10).
    - Updates selling_price if the item already exists (preserves current stock).
    Called whenever the LM saves rate governance or approves a new material request.
    """
    # Get all active warehouses
    warehouse_result = await db.execute(
        select(Warehouse).where(Warehouse.is_active == True)
    )
    warehouses = warehouse_result.scalars().all()

    for material in materials:
        name = material.get("name") or ""
        rate = float(material.get("rate") or 0)
        unit = material.get("unit") or "pcs"
        if not name:
            continue
        sku = _material_sku(name)

        for warehouse in warehouses:
            # Check if item already exists
            existing_result = await db.execute(
                select(InventoryItem).where(
                    InventoryItem.warehouse_id == warehouse.id,
                    InventoryItem.sku == sku,
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                # Only update the price; leave stock levels untouched
                existing.selling_price = rate
                db.add(existing)
            else:
                # Create a new inventory record with zero stock
                new_item = InventoryItem(
                    warehouse_id=warehouse.id,
                    sku=sku,
                    name=name,
                    category="Packing Materials",
                    unit=unit,
                    quantity_on_hand=0,
                    safety_stock=10,
                    cost_price=round(rate * 0.8, 2),
                    selling_price=rate,
                )
                db.add(new_item)

    await db.flush()


def _add_material_to_rates(material_name: str, rate: float, unit: str) -> None:
    """Add a new material to rates_config.json"""
    # Generate a camelCase id from the name
    material_id = "".join(
        word.capitalize() if i > 0 else word.lower()
        for i, word in enumerate(material_name.split())
    )
    
    # Load current rates
    if _RATES_CONFIG_PATH.exists():
        with open(_RATES_CONFIG_PATH, encoding="utf-8") as f:
            rates = json.load(f)
    else:
        rates = {}
    
    # Ensure materials is a list
    if not isinstance(rates.get("materials"), list):
        # Convert old dict format to list
        old_materials = rates.get("materials", {})
        rates["materials"] = [
            {"id": "box", "name": "Box", "rate": old_materials.get("box", 50), "unit": "pcs"},
            {"id": "bubbleWrap", "name": "Bubble Wrap", "rate": old_materials.get("bubbleWrap", 20), "unit": "m"},
            {"id": "crate", "name": "Crate Rental", "rate": old_materials.get("crate", 200), "unit": "pcs"},
        ]
    
    # Check if material already exists
    existing_ids = [m.get("id") for m in rates["materials"]]
    if material_id in existing_ids:
        # Update existing
        for m in rates["materials"]:
            if m.get("id") == material_id:
                m["rate"] = rate
                m["unit"] = unit
                break
    else:
        # Add new material
        rates["materials"].append({
            "id": material_id,
            "name": material_name,
            "rate": rate,
            "unit": unit,
        })
    
    # Save
    with open(_RATES_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(rates, f, indent=2)


async def approve_material_request(
    db: AsyncSession, request_id: UUID, data: MaterialRequestApprove, user: User
) -> MaterialRequestResponse:
    """LM approves a material request and auto-adds to rates config."""
    req = await _get_material_request(db, request_id)
    
    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING requests can be approved"
        )
    
    req.status = "APPROVED"
    req.approved_by = user.id
    req.approved_rate = data.approved_rate
    req.manager_notes = data.manager_notes
    
    db.add(req)
    await db.flush()
    await db.refresh(req)
    
    # Add material to rates config
    _add_material_to_rates(req.material_name, data.approved_rate, req.unit)

    # Sync the new material to inventory across all active warehouses
    await sync_packing_materials_to_inventory(
        db,
        [{"name": req.material_name, "rate": data.approved_rate, "unit": req.unit}],
    )

    # Fetch users for response
    requester = None
    if req.requested_by:
        user_result = await db.execute(select(User).where(User.id == req.requested_by))
        requester = user_result.scalar_one_or_none()
    
    return _to_material_request_response(req, requester, user)


async def reject_material_request(
    db: AsyncSession, request_id: UUID, data: MaterialRequestReject, user: User
) -> MaterialRequestResponse:
    """LM rejects a material request."""
    req = await _get_material_request(db, request_id)
    
    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING requests can be rejected"
        )
    
    req.status = "REJECTED"
    req.approved_by = user.id
    req.manager_notes = data.manager_notes
    
    db.add(req)
    await db.flush()
    await db.refresh(req)
    
    # Fetch users for response
    requester = None
    if req.requested_by:
        user_result = await db.execute(select(User).where(User.id == req.requested_by))
        requester = user_result.scalar_one_or_none()
    
    return _to_material_request_response(req, requester, user)
