# Backend maintenance scripts

Run each script from `backend/` as a module, so `app` is importable and it reads the same `.env` as the API.

```bash
python -m scripts.export_api_docs
```

| Script | What it does |
|---|---|
| `export_api_docs.py` | Writes `docs/openapi.json` and `docs/API_ENDPOINT_CATALOG.md` from the running app's schema |
| `seed_packing_materials.py` | Adds the PKG- packing material SKUs to every active hub that lacks them |
| `backfill_order_geocodes.py` | Geocodes orders saved without pickup or delivery coordinates |
| `fix_vehicle_documents.py` | Rewrites vehicle documents keyed by vehicle code to use the vehicle UUID |
| `migrate_inventory_prices.py` | Fills cost and selling prices on inventory rows created before prices existed |
| `create_test_order.py` | Creates an assigned order for trying the driver app end to end |
| `simulate_driver_movement.py` | Moves a test driver along a route so live tracking has data |
| `clear_dummy_data.py`, `delete_test_data.py` | Remove demo and test rows from a development database |

These scripts change data, so point `DATABASE_URL` at a development database before running them.
