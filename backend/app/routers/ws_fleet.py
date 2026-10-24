"""
WebSocket endpoint for real-time fleet location broadcasting and driver alerts.

Flow:
  1. Dashboard connects to ws://<host>/ws/fleet?token=<jwt>
  2. Backend validates JWT and adds connection to the pool
  3. When a driver POSTs a location update (REST), logistics_service calls
     fleet_manager.broadcast() which pushes the update to every connected dashboard.
  4. Dashboard updates map markers without waiting for the next 30-second poll.

Driver Alert Flow:
  1. Driver app connects to ws://<host>/ws/driver-alerts?token=<jwt>
  2. When dispatcher sends broadcast alert, driver_alert_manager.broadcast() pushes to all drivers.
  3. Driver app receives alert and shows notification.
"""
import asyncio
import contextlib
import json
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.utils.jwt import try_decode_token

router = APIRouter(tags=["Fleet WebSocket"])


class FleetConnectionManager:
    """Thread-safe WebSocket connection pool for fleet location broadcasts."""

    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.discard(ws)

    async def broadcast(self, payload: dict[str, Any]):
        """Send a JSON payload to every connected dashboard client."""
        if not self._connections:
            return
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        async with self._lock:
            targets = list(self._connections)
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        # Clean up dead connections
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


class DriverAlertManager:
    """Thread-safe WebSocket connection pool for driver alert broadcasts."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}  # driver_id -> websocket
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, driver_id: str):
        await ws.accept()
        async with self._lock:
            # Close existing connection if any
            old_ws = self._connections.get(driver_id)
            if old_ws:
                with contextlib.suppress(Exception):
                    await old_ws.close()
            self._connections[driver_id] = ws

    async def disconnect(self, driver_id: str):
        async with self._lock:
            self._connections.pop(driver_id, None)

    async def broadcast(self, payload: dict[str, Any]):
        """Send a JSON payload to all connected driver clients."""
        if not self._connections:
            return
        message = json.dumps(payload)
        dead: list[str] = []
        async with self._lock:
            targets = list(self._connections.items())
        for driver_id, ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(driver_id)
        # Clean up dead connections
        if dead:
            async with self._lock:
                for driver_id in dead:
                    self._connections.pop(driver_id, None)

    async def send_to_driver(self, driver_id: str, payload: dict[str, Any]):
        """Send a JSON payload to a specific driver."""
        async with self._lock:
            ws = self._connections.get(driver_id)
        if ws:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                async with self._lock:
                    self._connections.pop(driver_id, None)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Singletons used across the whole app
fleet_manager = FleetConnectionManager()
driver_alert_manager = DriverAlertManager()


async def _authenticate_ws_token(token: str | None) -> bool:
    """Return True if the JWT token is valid (any authenticated user)."""
    return try_decode_token(token) is not None


async def _decode_ws_token(token: str | None) -> dict | None:
    """Decode JWT token and return payload with user_id (sub)."""
    return try_decode_token(token)


@router.websocket("/ws/fleet")
async def fleet_websocket(
    ws: WebSocket,
    token: str | None = Query(default=None),
):
    """
    WebSocket endpoint for live fleet tracking.

    Connect with:
        ws://<host>/ws/fleet?token=<access_token>

    Messages from server (JSON):
        { "type": "location_update", "driver_id": "...", "driver_name": "...",
          "latitude": 0.0, "longitude": 0.0, "status": "...",
          "vehicle_code": "...", "vehicle_id": "...", "last_updated": "..." }
        { "type": "ping" }

    Messages from client:
        { "type": "pong" }  (keepalive response, ignored)
    """
    if not await _authenticate_ws_token(token):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await fleet_manager.connect(ws)
    # Send a welcome message so the client knows the connection is live
    await ws.send_text(json.dumps({"type": "connected", "message": "Fleet WebSocket connected"}))

    try:
        while True:
            # Keep connection open; client may send pong frames
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            except TimeoutError:
                # Send a ping every 30 s to keep the connection alive through proxies
                try:
                    await ws.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await fleet_manager.disconnect(ws)


@router.websocket("/ws/driver-alerts")
async def driver_alerts_websocket(
    ws: WebSocket,
    token: str | None = Query(default=None),
):
    """
    WebSocket endpoint for driver alert notifications.

    Connect with:
        ws://<host>/ws/driver-alerts?token=<access_token>

    Messages from server (JSON):
        { "type": "alert", "severity": "critical|high|warning|info",
          "title": "...", "message": "...", "timestamp": "..." }
        { "type": "crisis_update", "alert_id": "...", "status": "...", ... }
        { "type": "ping" }

    Messages from client:
        { "type": "pong" }  (keepalive response, ignored)
        { "type": "ack", "alert_id": "..." }  (acknowledge receipt of alert)
    """
    payload = await _decode_ws_token(token)
    if not payload:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    driver_id = payload.get("sub", "unknown")
    await driver_alert_manager.connect(ws, driver_id)
    # Send a welcome message so the client knows the connection is live
    await ws.send_text(json.dumps({"type": "connected", "message": "Driver alerts WebSocket connected", "driver_id": driver_id}))

    try:
        while True:
            # Keep connection open; client may send pong frames or ack messages
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                # Handle ack messages if needed (currently just ignored)
                try:
                    data = json.loads(msg)
                    if data.get("type") == "pong":
                        pass  # Keepalive response, no action needed
                except Exception:
                    pass
            except TimeoutError:
                # Send a ping every 30 s to keep the connection alive through proxies
                try:
                    await ws.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await driver_alert_manager.disconnect(driver_id)
