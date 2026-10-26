"""Fills the proof-of-delivery HTML template with one order's details.

Customers type their names and addresses, so every value goes through html.escape
before it lands in the page. Image values only ever fill a quoted src attribute.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from app.schemas.orders import OrderResponse

TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "ProofOfDelivery.html"


def _image_src(value: str, default_mime: str) -> str:
    """A data URI for a stored image, escaped for a double-quoted attribute."""
    data = value if value.startswith("data:") else f"data:{default_mime};base64,{value}"
    return escape(data, quote=True)


def _photo_slot_html(photo: str | None, slot_id: str, alt_text: str) -> str:
    if photo:
        return (
            f'<div id="{slot_id}" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2 overflow-hidden">'
            f'<img src="{_image_src(photo, "image/jpeg")}" alt="{alt_text}" class="w-full h-full object-cover"/>'
            "</div>"
        )
    return (
        f'<div id="{slot_id}" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2">'
        '<span class="text-[35px]">📷</span>'
        "</div>"
    )


def render_proof_of_delivery_html(order: OrderResponse) -> str:
    html_content = TEMPLATE_PATH.read_text(encoding="utf-8")

    driver_name = order.assigned_driver_name or "Driver"
    driver_code = f"DRV-{str(order.assigned_driver_id)[-4:]}" if order.assigned_driver_id else ""

    delivery_date = "N/A"
    delivery_time = "N/A"
    delivery_dt_source = order.delivered_at or order.service_otp_verified_at or order.scheduled_at or order.created_at
    if delivery_dt_source:
        dt = datetime.fromisoformat(str(delivery_dt_source)) if isinstance(delivery_dt_source, str) else delivery_dt_source
        delivery_date = dt.strftime("%B %d, %Y")
        delivery_time = dt.strftime("%I:%M %p").upper()

    customer_name = order.customer_name or "Customer"
    customer_phone = order.customer_phone or "N/A"

    # The template shows the street line, then city and state with PIN.
    delivery_address_parts = (order.delivery_addr or "N/A").split(",")
    delivery_address = delivery_address_parts[0].strip() if delivery_address_parts else "N/A"
    delivery_city = delivery_address_parts[1].strip() if len(delivery_address_parts) > 1 else ""
    delivery_state_zip = delivery_address_parts[2].strip() if len(delivery_address_parts) > 2 else ""

    driver_display = f"{driver_name} ({driver_code})" if driver_code else driver_name

    signature_source = order.poc_signature or order.pod_signature
    signature_html = '<div class="text-center text-gray-400 text-xs flex items-center justify-center h-full">No signature captured</div>'
    if signature_source and signature_source.strip():
        signature_html = f'<img src="{_image_src(signature_source, "image/png")}" alt="Customer Signature" class="w-full h-full object-contain"/>'

    signature_box_html = (
        '<div id="pod-sig" class="border-2 border-gray-400 rounded h-[60px] bg-white mb-2 overflow-hidden flex items-center justify-center">'
        f"{signature_html}"
        "</div>"
    )

    photos = order.pod_photos or []
    text_values = {
        "CC-12345": str(order.tracking_code) if order.tracking_code else str(order.id)[:8].upper(),
        "December 20, 2024 - 01:45 PM": f"{delivery_date} - {delivery_time}" if delivery_date != "N/A" and delivery_time != "N/A" else delivery_date,
        "December 20, 2024": delivery_date,
        "01:45 PM": delivery_time,
        "Sarah Khan | +91 98765 43210": f"{customer_name} | {customer_phone}",
        "Sarah Khan": customer_name,
        "+91 98765 43210": customer_phone,
        "Prakash Reddy (DRV-8765)": driver_display,
        "456 Maple Avenue, Indiranagar": delivery_address,
        "Bangalore, Karnataka - 560038": f"{delivery_city}, {delivery_state_zip}".strip(" ,-") if delivery_city else delivery_state_zip,
        "Name: Sarah Khan": f"Name: {customer_name}",
    }
    markup_values = {
        '<div id="pod-sig" class="border-2 border-gray-400 rounded h-[60px] bg-white mb-2"></div>': signature_box_html,
        '<div id="pod-p1" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span></div>':
            _photo_slot_html(photos[0] if len(photos) > 0 else None, "pod-p1", "Before Unloading"),
        '<div id="pod-p2" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span></div>':
            _photo_slot_html(photos[1] if len(photos) > 1 else None, "pod-p2", "Items at Location"),
        '<div id="pod-p3" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span></div>':
            _photo_slot_html(photos[2] if len(photos) > 2 else None, "pod-p3", "After Placement"),
    }

    # Placeholders are replaced in this order, longest first where one contains another.
    for placeholder, value in text_values.items():
        html_content = html_content.replace(placeholder, escape(value, quote=True))
    for placeholder, markup in markup_values.items():
        html_content = html_content.replace(placeholder, markup)
    return html_content
