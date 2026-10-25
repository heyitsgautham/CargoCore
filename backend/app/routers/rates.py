"""
rates.py
GET  /api/v1/rates                  — public, returns current rate config
PUT  /api/v1/rates                  — LOGISTIC_MANAGER only, persists new config
GET  /api/v1/rates/inventory-seeded — LM only, checks if packing materials exist in inventory
POST /api/v1/rates/seed-inventory   — LM only, one-time seed packing materials to all warehouses
"""
import json
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.inventory import InventoryItem
from app.services.material_request_service import sync_packing_materials_to_inventory

router = APIRouter(prefix="/api/v1/rates", tags=["Rates"])

# Stored beside the backend package (project root)
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "rates_config.json"

_DEFAULTS: dict[str, Any] = {
    # ── Customer charges (used by CreateShipment, BookMove, etc.) ──────────
    "baseBookingFee": 220,          # flat base fee for vendor shipments
    "perKmRate": 12,                # ₹/km for vendor shipments
    "minimumCharge": 500,
    "expressMultiplier": 1.5,
    "customerLaborRate": 250,       # ₹ per helper (vendor shipments)
    "customerPackingFee": 200,      # flat packing fee (vendor shipments)
    "insurancePct": 3,              # insurance as % of declared value
    "materials": [
        {"id": "box", "name": "Box", "rate": 50, "unit": "pcs"},
        {"id": "bubbleWrap", "name": "Bubble Wrap", "rate": 20, "unit": "m"},
        {"id": "crate", "name": "Crate Rental", "rate": 200, "unit": "pcs"},
    ],
    # ── Individual / House-shift (used by BookMove → individualStore) ──────
    "individualBookingFee": 300,    # fixed base booking charge
    "individualLaborRate": 800,     # ₹ per helper (house-shift)
    "individualPackingPct": 20,     # packing = X% of base fare
    "individualDistanceRates": {
        "miniTruck": 18,
        "tempo": 25,
        "lcv": 35,
        "hcv": 50,
    },
    "smallPackagePerKgRate": 120,   # ₹/kg for small packages
    "smallPackagePerKmRate": 12,    # ₹/km delivery for small packages
    # ── Driver / Payroll ──────────────────────────────────────────────────
    "driver": {
        "type": "salary_bonus",
        "baseSalary": 25000,
        "hra": 5000,
        "da": 2000,
        "performanceBonus": 3000,
        "kmRate": 15,
        "fuelIncentive": 500,
        "ratingMultiplier": 1.1,
    },
    "labor": {
        "baseSalary": 18000,
        "hra": 3500,
        "da": 1500,
        "performanceBonus": 2000,
        "hourlyWage": 150,
        "overtimeMul": 1.5,
        "fieldAllowance": 200,
    },
    "managers": {
        "warehouseBase": 65000,
        "warehouseHra": 15000,
        "warehouseDa": 5000,
        "warehouseBonus": 10000,
        "dispatcherBase": 45000,
        "dispatcherHra": 10000,
        "dispatcherDa": 4000,
        "dispatcherBonus": 8000,
    },
    # ── Fuel ──────────────────────────────────────────────────────────────
    "fuel": {
        "maxClaimPerKm": 12.5,
        "benchmarkMileage": 8.5,
    },
    # ── Dynamic / surge ───────────────────────────────────────────────────
    "dynamic": {
        "peak": 1.2,
        "emergency": 2.5,
    },
}


def _load() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                stored = json.load(f)
            # Deep-merge stored over defaults so new keys always appear
            merged = {**_DEFAULTS}
            for k, v in stored.items():
                if isinstance(v, dict) and isinstance(merged.get(k), dict):
                    merged[k] = {**merged[k], **v}
                else:
                    merged[k] = v
            return merged
        except Exception:
            pass
    return dict(_DEFAULTS)


def _save(data: dict[str, Any]) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.get("", summary="Get current rate configuration")
async def get_rates() -> dict[str, Any]:
    return _load()


@router.put(
    "",
    summary="Update rate configuration (LOGISTIC_MANAGER only)",
    dependencies=[Depends(require_role("LOGISTIC_MANAGER"))],
)
async def update_rates(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty payload")
    current = _load()
    # Deep-merge incoming payload over current
    for k, v in payload.items():
        if isinstance(v, dict) and isinstance(current.get(k), dict):
            current[k] = {**current[k], **v}
        else:
            current[k] = v
    _save(current)
    return current


@router.get(
    "/inventory-seeded",
    summary="Check if packing materials have been seeded to inventory (LOGISTIC_MANAGER only)",
    dependencies=[Depends(require_role("LOGISTIC_MANAGER"))],
)
async def check_inventory_seeded(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    result = await db.execute(
        select(func.count(InventoryItem.id)).where(
            InventoryItem.category == "Packing Materials",
            InventoryItem.sku.like("PKG-%"),
        )
    )
    count = result.scalar_one()
    return {"seeded": count > 0}


@router.post(
    "/seed-inventory",
    summary="One-time seed packing materials from rate governance to all warehouse inventories (LOGISTIC_MANAGER only)",
    dependencies=[Depends(require_role("LOGISTIC_MANAGER"))],
)
async def seed_inventory(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    # Guard: if already seeded, do nothing
    count_result = await db.execute(
        select(func.count(InventoryItem.id)).where(
            InventoryItem.category == "Packing Materials",
            InventoryItem.sku.like("PKG-%"),
        )
    )
    if count_result.scalar_one() > 0:
        return {"seeded": True, "already_done": True, "message": "Packing materials already exist in inventory"}

    materials = _load().get("materials", [])
    if not materials:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No materials defined in rate governance")

    await sync_packing_materials_to_inventory(db, materials)
    return {"seeded": True, "already_done": False, "message": f"Seeded {len(materials)} materials to all active warehouses"}
