// Leaflet marker icons and coordinate parsing for the order clustering map.

/** "12.97, 77.59" becomes { lat, lng }, anything else null. */
export function parseLatLng(locationStr) {
    if (!locationStr || typeof locationStr !== 'string') return null
    const parts = locationStr.split(',').map(s => parseFloat(s.trim()))
    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) return { lat: parts[0], lng: parts[1] }
    return null
}

export function makeDriverIcon(L, status) {
    const color = ['On Trip', 'IN_TRANSIT', 'Busy'].includes(status) ? '#facc15' : '#4ade80'
    return L.divIcon({
        className: '',
        html: `<div style="width:32px;height:32px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
                 <span style="font-size:14px;">🚚</span>
               </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    })
}

export function makeOrderIcon(L) {
    return L.divIcon({
        className: '',
        html: `<div style="width:28px;height:28px;border-radius:50%;background:#f97316;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
                 <span style="font-size:12px;">📦</span>
               </div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 28],
    })
}

export function makeDeliveryIcon(L) {
    return L.divIcon({
        className: '',
        html: `<div style="width:24px;height:24px;border-radius:50%;background:#60a5fa;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
                 <span style="font-size:10px;">🏁</span>
               </div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 24],
    })
}
