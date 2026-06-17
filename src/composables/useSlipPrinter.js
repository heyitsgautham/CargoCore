/**
 * useSlipPrinter — opens CargoCore HTML slips with real data injected.
 * Fetches HTML at runtime from /html-slips/ (served by Vite plugin).
 */

import { buildPodData } from '@/utils/pod'

const SLIP_FILES = {
  bookingConfirmation:    'BookingConfirmation.html',
  finalTaxInvoice:        'FinalTaxInvoice.html',
  instantQuotation:       'InstantQuotation.html',
  proofOfDelivery:        'ProofOfDelivery.html',
  tripManifest:           'TripManifest.html',
  digitalPickList:        'DigitalPickList.html',
  laborAssignment:        'LaborAssignment.html',
  salarySlip:             'SalarySlip.html',
  financeTransaction:     'FinanceTransactionSlip.html',
  vehicleSafetyChecklist: 'VehicleSafetyChecklist.html',
  assetCheckout:          'AssetCheckout.html',
  aiVolumeEstimate:       'AIVolumeEstimate.html',
}

export const SLIP_LABELS = {
  bookingConfirmation:    'Booking Confirmation',
  finalTaxInvoice:        'Tax Invoice',
  instantQuotation:       'Instant Quotation',
  proofOfDelivery:        'Proof of Delivery',
  tripManifest:           'Trip Manifest',
  digitalPickList:        'Digital Pick List',
  laborAssignment:        'Labour Assignment',
  salarySlip:             'Salary Slip',
  financeTransaction:     'Finance Transaction Slip',
  vehicleSafetyChecklist: 'Safety Checklist',
  assetCheckout:          'Asset Checkout',
  aiVolumeEstimate:       'AI Volume Estimate',
}

export const SLIP_ICONS = {
  bookingConfirmation:    'receipt_long',
  finalTaxInvoice:        'request_quote',
  instantQuotation:       'calculate',
  proofOfDelivery:        'verified',
  tripManifest:           'assignment',
  digitalPickList:        'checklist',
  laborAssignment:        'engineering',
  salarySlip:             'payments',
  financeTransaction:     'receipt_long',
  vehicleSafetyChecklist: 'health_and_safety',
  assetCheckout:          'inventory_2',
  aiVolumeEstimate:       'model_training',
}

// ─── module-level HTML cache (survives across composable calls) ───────────────
const _htmlCache = new Map()

// ─── helpers ──────────────────────────────────────────────────────────────────

function inr(n) {
  return `₹${Number(n || 0).toLocaleString('en-IN')}`
}

function fmtShort(value) {
  if (!value) return 'TBD'
  const d = new Date(value)
  if (isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function fmtLong(value) {
  if (!value) return fmtShort(new Date())
  const d = new Date(value)
  if (isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })
}

function fmtTime(value) {
  if (!value) return 'TBD'
  const d = new Date(value)
  if (isNaN(d.getTime())) return String(value)
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase()
}

function num(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function cleanText(value, fallback = '—') {
  const text = String(value ?? '').trim()
  return text || fallback
}

function compactAddress(address, fallback = '—') {
  const parts = String(address ?? '')
    .split(',')
    .map(part => part.trim())
    .filter(Boolean)
  return parts.length ? parts.join(', ') : fallback
}

function routeLabel(address, fallback = '—') {
  const parts = String(address ?? '')
    .split(',')
    .map(part => part.trim())
    .filter(Boolean)
  if (!parts.length) return fallback
  return parts.slice(0, 2).join(', ')
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const values = [lat1, lon1, lat2, lon2].map(Number)
  if (values.some(value => !Number.isFinite(value))) return null
  const [aLat, aLon, bLat, bLon] = values
  const toRad = (deg) => (deg * Math.PI) / 180
  const earthRadiusKm = 6371
  const dLat = toRad(bLat - aLat)
  const dLon = toRad(bLon - aLon)
  const q =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) * Math.sin(dLon / 2) ** 2
  return 2 * earthRadiusKm * Math.asin(Math.sqrt(q))
}

function estimateDistanceKm(order) {
  const direct = num(
    order?.distanceKm ??
    order?.distance_km ??
    order?.totalDistance ??
    order?.total_distance ??
    order?.routeDistanceKm,
    NaN
  )
  if (Number.isFinite(direct) && direct > 0) return direct

  const geo = haversineKm(order?.pickupLat, order?.pickupLng, order?.deliveryLat, order?.deliveryLng)
  if (geo && geo > 0) return geo * 1.24
  return null
}

function formatDistance(distanceKm) {
  if (!distanceKm || !Number.isFinite(distanceKm)) return 'Route based on dispatch plan'
  return `Distance: ${distanceKm.toFixed(distanceKm >= 100 ? 0 : 1)} km`
}

function estimateLoadMinutes(order) {
  return Math.max(30, 45 + num(order?.laborCount) * 15)
}

function estimateUnloadMinutes(order) {
  return Math.max(25, 35 + num(order?.laborCount) * 10)
}

function estimateTravelMinutes(distanceKm, vehicleType = '') {
  if (!distanceKm || !Number.isFinite(distanceKm)) return 45
  const speed = /truck|xl|heavy/i.test(vehicleType) ? 28 : /van/i.test(vehicleType) ? 34 : 30
  return Math.max(25, Math.round((distanceKm / speed) * 60))
}

function formatDuration(minutes) {
  if (!Number.isFinite(minutes) || minutes <= 0) return 'TBD'
  const hours = minutes / 60
  return hours >= 1 ? `${hours.toFixed(1)} hrs` : `${Math.round(minutes)} min`
}

function estimateFuelLiters(distanceKm, vehicleType = '') {
  if (!distanceKm || !Number.isFinite(distanceKm)) return null
  const efficiency = /truck|xl|heavy/i.test(vehicleType) ? 5.5 : /van/i.test(vehicleType) ? 9 : 7
  return Math.max(1, Math.round((distanceKm / efficiency) * 10) / 10)
}

function vehicleCapacityLabel(vehicleType = '', weight = 0) {
  if (/truck|xl|heavy/i.test(vehicleType) || weight > 1800) return '3.5 Tons'
  if (/van/i.test(vehicleType) || weight > 900) return '2.0 Tons'
  return '1.0 Ton'
}

function estimateBoxes(order) {
  const explicit = num(order?.boxCount ?? order?.boxes ?? order?.itemsCount ?? order?.itemCount, NaN)
  if (Number.isFinite(explicit) && explicit > 0) return explicit
  const volume = num(order?.volume ?? order?.cargoVolume ?? order?.cargo_volume_m3, NaN)
  if (Number.isFinite(volume) && volume > 0) return Math.max(1, Math.round(volume * 8))
  const weight = num(order?.weight)
  return Math.max(1, Math.round(weight / 35) || 1)
}

function summarizeSpecialItems(order) {
  const notes = String(order?.specialInstructions || order?.notes || '').toLowerCase()
  const tags = []
  if (notes.includes('fragile')) tags.push('Fragile')
  if (notes.includes('priority')) tags.push('Priority')
  if (notes.includes('perishable')) tags.push('Perishable')
  if (num(order?.laborCount) > 0) tags.push(`${num(order?.laborCount)} crew`)
  return tags.length ? tags.join(' • ') : cleanText(order?.cargoType || order?.type, 'Standard cargo')
}

function routeViaLabel(order, vehicleNo) {
  const pickup = routeLabel(order?.pickupAddr, '')
  const delivery = routeLabel(order?.deliveryAddr, '')
  if (pickup && delivery) return `Via dispatch route from ${pickup} to ${delivery}`
  return `Assigned vehicle: ${vehicleNo}`
}

function buildTripSchedule(order) {
  const base = new Date(order?.scheduledAt || order?.eta || order?.createdAt || order?.lastUpdated || Date.now())
  const distanceKm = estimateDistanceKm(order)
  const loadMinutes = estimateLoadMinutes(order)
  const unloadMinutes = estimateUnloadMinutes(order)
  const travelMinutes = estimateTravelMinutes(distanceKm, order?.vehicleType || order?.vehicle)
  const pickup = new Date(base.getTime())
  const delivery = new Date(base.getTime() + (loadMinutes + travelMinutes) * 60_000)
  const depot = new Date(delivery.getTime() + (unloadMinutes + Math.round(travelMinutes * 0.55)) * 60_000)
  return {
    pickupTime: fmtTime(pickup),
    deliveryTime: fmtTime(delivery),
    returnTime: fmtTime(depot),
    loadTime: `${loadMinutes} minutes`,
    unloadTime: `${unloadMinutes} minutes`,
    totalDuration: formatDuration(loadMinutes + unloadMinutes + travelMinutes),
    routeMeta: `${formatDistance(distanceKm)} | Est. Time: ${formatDuration(travelMinutes)}`,
    totalDistance: distanceKm ? `${distanceKm.toFixed(distanceKm >= 100 ? 0 : 1)} km` : 'TBD',
    fuelEstimate: estimateFuelLiters(distanceKm, order?.vehicleType || order?.vehicle),
  }
}

function assetCode(label, index) {
  const prefix = String(label || '')
    .split(/[^A-Za-z0-9]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0].toUpperCase())
    .join('') || 'AK'
  return `${prefix}-${String(index + 1).padStart(3, '0')}`
}

function defaultAssetQuantities(order) {
  const weight = Math.max(0, num(order?.weight))
  const laborCount = Math.max(0, num(order?.laborCount))
  return {
    'Moving Boxes': Math.max(6, Math.round(weight / 35) || 6),
    'Bubble Wrap (rolls)': Math.max(1, Math.ceil(weight / 250) || 1),
    'Moving Blankets': Math.max(2, laborCount * 2 || 2),
    'Dollies / Hand Trucks': Math.max(1, Math.ceil(weight / 350) || 1),
    'Tape Rolls': Math.max(2, laborCount + 1 || 2),
    'Stretch Wrap (rolls)': Math.max(1, Math.ceil(weight / 400) || 1),
    'Furniture Pads': Math.max(2, laborCount * 2 || 2),
  }
}

function buildAssetEquipment(order) {
  const defaults = defaultAssetQuantities(order)
  const provided = Array.isArray(order?.assetItems) ? order.assetItems : []

  const normalized = provided.map((item, index) => {
    const label = cleanText(item?.label || item?.name, `Asset ${index + 1}`)
    const qty = Math.max(0, num(item?.qty ?? item?.sentOut ?? item?.count, defaults[label] || 0))
    return {
      label,
      id: cleanText(item?.id || item?.assetId, assetCode(label, index)),
      qty: qty || defaults[label] || 0,
      cond: cleanText(item?.cond || item?.condition || item?.status, 'Ready'),
    }
  }).filter(item => item.qty > 0)

  if (normalized.length) return normalized

  return Object.entries(defaults).map(([label, qty], index) => ({
    label,
    id: assetCode(label, index),
    qty,
    cond: 'Ready',
  }))
}

function applyReplacements(html, map) {
  for (const [from, to] of Object.entries(map)) {
    if (from) html = html.split(from).join(to ?? '—')
  }
  return html
}

function fixAssetPaths(html) {
  // relative paths from html-slips/ → absolute URLs (needed for Blob URL context)
  return html
    .replace(/\.\.\/src\/assets\//g, '/src/assets/')
    .replace(/(src|href)="assets\//g, '$1="/html-slips/assets/')
}

function openBlobHtml(html, targetWindow = null) {
  // Store in localStorage so the slip survives browser refresh.
  // Blob URLs cannot be refreshed in Chrome (ERR_FILE_NOT_FOUND).
  const key = '__cargo_slip_' + Date.now()
  try {
    // Prune stale slip entries older than 2 hours to avoid bloating storage
    for (const k of Object.keys(localStorage)) {
      if (!k.startsWith('__cargo_slip_')) continue
      const ts = Number(k.replace('__cargo_slip_', ''))
      if (Date.now() - ts > 2 * 60 * 60 * 1000) localStorage.removeItem(k)
    }
    localStorage.setItem(key, html)
    if (targetWindow && !targetWindow.closed) {
      targetWindow.location.href = `/slip-preview?k=${key}`
      return
    }
    window.open(`/slip-preview?k=${key}`, '_blank')
  } catch {
    // localStorage full — fall back to blob (no refresh support)
    const blob = new Blob([html], { type: 'text/html; charset=utf-8' })
    const blobUrl = URL.createObjectURL(blob)
    if (targetWindow && !targetWindow.closed) {
      targetWindow.location.href = blobUrl
      return
    }
    window.open(blobUrl, '_blank')
  }
}

async function fetchSlipHtml(key) {
  if (_htmlCache.has(key)) return _htmlCache.get(key)
  const file = SLIP_FILES[key]
  if (!file) return null
  try {
    const res = await fetch(`/html-slips/${file}`)
    if (!res.ok) return null
    const html = await res.text()
    _htmlCache.set(key, html)
    return html
  } catch {
    return null
  }
}

// ─── per-slip replacement maps ────────────────────────────────────────────────

function bookingConfirmationReplacements(order, user) {
  const total      = Number(order?.amount || order?.cost?.total || 0)
  const paid       = Number(order?.paidAmount || 0)
  const balance    = Math.max(0, total - paid)
  const advancePct = total > 0 ? Math.round((paid / total) * 100) : 0
  const origin     = order?.origin || order?.pickup || '—'
  const dest       = order?.destination || '—'

  return {
    'CC-12345':                     order?.id || '—',
    'December 16, 2024':            order?.createdAt || order?.date || fmtShort(new Date()),
    'December 20, 2024':            order?.eta || 'TBD',
    '09:00 AM - 12:00 PM':          order?.serviceTimeBlock || 'Flexible',
    'Sarah Khan':                   user?.name || '—',
    '+91 98765 43210':              user?.phone || '—',
    'sarah.khan@email.com':         user?.email || '—',
    '+91 87654 32109':              '—',
    '123 Oak Street, Whitefield':   origin,
    'Bangalore, Karnataka - 560066':'',
    '456 Maple Avenue, Indiranagar':dest,
    'Bangalore, Karnataka - 560038':'',
    'Floor: Ground | Lift: Available':'',
    'Floor: 2nd | Lift: Available': '',
    '₹4,500':                       inr(total),
    '₹1,350':                       inr(paid),
    'Advance Paid (30%)':           `Advance Paid${advancePct > 0 ? ` (${advancePct}%)` : ''}`,
    'UPI / Online Transfer':        order?.paymentMode || order?.paymentMode || 'Invoice',
    'TXN20241216789456':            order?.id || '—',
    '₹3,150':                       inr(balance),
    '4 skilled workers':            order?.laborCount > 0 ? `${order.laborCount} workers` : 'On-demand',
    '14 ft covered truck':          order?.vehicle || order?.vehicleType || 'Assigned vehicle',
  }
}

function finalTaxInvoiceReplacements(order, user) {
  const total    = Number(order?.amount ?? order?.cost?.total ?? order?.total_amount ?? 0)
  const rawPaid  = Number(order?.paidAmount ?? order?.paid_amount ?? 0)
  const base     = Number(order?.cost?.base   || (total * 0.40))
  const labor    = Number(order?.cost?.labor  || (total * 0.35))
  const mats     = Number(order?.cost?.materials || (total * 0.15))
  const packing  = Number(order?.cost?.packing   || (total * 0.10))
  const paymentStatus = String(order?.paymentStatus || order?.payment_status || '').toLowerCase()
  const paymentMode = order?.paymentMode || order?.payment_mode || 'Online'
  const invoiceDateSource = order?.deliveredAt || order?.delivered_at || order?.createdAt || order?.date || new Date()
  const billToName = order?.customerName || order?.customer_name || user?.name || '—'
  const billToPhone = order?.customerPhone || order?.customer_phone || user?.phone || '—'
  const billToEmail = order?.customerEmail || order?.customer_email || user?.email || '—'
  const origin   = order?.origin || order?.pickup || '—'
  const dest     = order?.destination || '—'
  const vehicle  = order?.vehicle || order?.vehicleType || 'Vehicle'

  function formatLongDate(value) {
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return String(value || fmtShort(new Date()))
    return d.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' })
  }

  function formatShortDate(value) {
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return String(value || fmtShort(new Date()))
    return d.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  const dateStr  = formatLongDate(invoiceDateSource)
  const shortDateStr = formatShortDate(invoiceDateSource)

  let paid = rawPaid
  if (paid <= 0 && ['paid', 'completed'].includes(paymentStatus)) {
    paid = total
  }
  if (paid < 0) paid = 0
  if (total > 0 && paid > total) paid = total

  const balanceSafe = Math.max(0, total - paid)

  // payment status badge + banner text
  const isPaid = total > 0
    ? (paid >= total || ['paid', 'completed'].includes(paymentStatus))
    : ['paid', 'completed'].includes(paymentStatus)
  const isPartial = !isPaid && (paid > 0 || paymentStatus === 'partial')
  const statusBadge  = isPaid ? 'PAID' : isPartial ? 'PARTIAL' : 'UNPAID'
  const statusBanner = isPaid ? '✓ PAID IN FULL' : isPartial ? '⏳ PARTIALLY PAID' : '⚠ PAYMENT PENDING'
  const statusClass = isPaid
    ? 'font-semibold text-green-600'
    : isPartial
      ? 'font-semibold text-amber-600'
      : 'font-semibold text-red-600'
  // Change banner color class based on status
  const bannerClass  = isPaid
    ? 'inline-block bg-green-600 text-white px-8 py-3 rounded-lg'
    : isPartial
    ? 'inline-block bg-amber-500 text-white px-8 py-3 rounded-lg'
    : 'inline-block bg-red-600 text-white px-8 py-3 rounded-lg'

  const paidPercent = total > 0 ? Math.round((paid / total) * 100) : 0
  const firstPaymentLabel = isPaid
    ? 'Full Payment (100%)'
    : isPartial
      ? `Partial Payment (${paidPercent}%)`
      : 'Payment Pending'
  const secondPaymentLabel = balanceSafe > 0 ? 'Balance Due' : 'Balance Cleared'
  const firstPaymentMode = (isPaid || isPartial) ? paymentMode : '—'
  const secondPaymentMode = balanceSafe > 0 ? paymentMode : '—'

  return {
    // Invoice meta
    'INV-2024-12-0567':           `INV-${order?.id || '—'}`,
    'December 20, 2024':          dateStr,
    'CC-12345':                   order?.id || '—',
    // Payment status banner
    'inline-block bg-green-600 text-white px-8 py-3 rounded-lg': bannerClass,
    '✓ PAID IN FULL':             statusBanner,
    'font-semibold text-green-600': statusClass,
    // Status cell (small text in invoice details table)
    '>PAID<':                     `>${statusBadge}<`,
    // Customer
    'Sarah Khan':                 billToName,
    '+91 98765 43210':            billToPhone,
    'sarah.khan@email.com':       billToEmail,
    '456 Maple Avenue, Indiranagar': dest,
    'Bangalore, Karnataka - 560038': '',
    // Route
    '123 Oak Street, Whitefield': origin,
    'Bangalore, Karnataka - 560066': '',
    '14 ft covered truck, 18.5 km distance':
      `${vehicle} · ${origin.split(',')[0]} → ${dest.split(',')[0]}`,
    'From: 123 Oak Street, Whitefield to 456 Maple Avenue, Indiranagar': '',
    // Labor
    '4 skilled workers for loading &amp; unloading':
      order?.laborCount > 0 ? `${order.laborCount} workers` : 'On-demand labour',
    // Service line amounts (table cells: >value<)
    '>1,800.00<':  `>${base.toFixed(2)}<`,
    '>1,600.00<':  `>${labor.toFixed(2)}<`,
    '>700.00<':    `>${mats.toFixed(2)}<`,
    '>400.00<':    `>${packing.toFixed(2)}<`,
    // Subtotal + GST table amounts
    '>4,500.00<':  `>${total.toFixed(2)}<`,
    // Amount summary (with ₹ prefix)
    '₹4,500.00':   `₹${total.toFixed(2)}`,
    // Payment rows
    '>1,350.00<':  `>${paid.toFixed(2)}<`,
    '>3,150.00<':  `>${balanceSafe.toFixed(2)}<`,
    'Advance Payment (30%)': firstPaymentLabel,
    'Balance Payment (70%)': secondPaymentLabel,
    '>UPI<':       `>${firstPaymentMode}<`,
    '>Cash<':      `>${secondPaymentMode}<`,
    // Declared value / insurance coverage
    'Coverage up to ₹50,000': order?.declaredValue > 0 ? `Coverage up to ${inr(order.declaredValue)}` : 'Coverage up to ₹50,000',
    // Amount in words (approximate)
    'Four Thousand Five Hundred Rupees Only':
      `${inr(total)} — ${isPaid ? 'Paid in Full' : isPartial ? `Paid: ${inr(paid)} · Pending: ${inr(balanceSafe)}` : 'Payment Pending'}`,
    // Date fields in payment table
    'Dec 16, 2024': shortDateStr,
    'Dec 20, 2024': balanceSafe > 0 ? formatShortDate(order?.eta || invoiceDateSource) : shortDateStr,
  }
}

function proofOfDeliveryReplacements(order, user) {
  const pod = buildPodData(order, {
    timestamp: order?.deliveredAt || order?.delivered_at || order?.pod?.timestamp || order?.eta || order?.createdAt || order?.date || null,
    location: order?.pod?.location || order?.destination || order?.delivery_addr || '—',
    signedByFallback: user?.name || 'Receiver',
  })
  const photos = pod.photos
  const signature = pod.signature || null
  const driverName = order?.driver || order?.assigned_driver_name || order?.driver_name || '—'
  const signedBy = pod.signedBy || order?.customerName || order?.customer_name || user?.name || '—'
  const customerPhone = order?.customerPhone || order?.customer_phone || user?.phone || '—'
  const deliveryAddress = pod.location || order?.destination || order?.delivery_addr || '—'
  const deliveryStamp = order?.deliveredAt || order?.delivered_at || pod.timestamp || order?.eta || order?.createdAt || order?.date || null

  function asDataUrl(value, mimeType) {
    if (!value) return null
    return String(value).startsWith('data:') ? String(value) : `data:${mimeType};base64,${value}`
  }

  function podDate(value) {
    if (!value) return fmtShort(new Date())
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return String(value)
    return d.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' })
  }

  function podTime(value) {
    if (!value) return '—'
    const d = new Date(value)
    if (Number.isNaN(d.getTime())) return '—'
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase()
  }

  const deliveryDate = podDate(deliveryStamp)
  const deliveryTime = podTime(deliveryStamp)
  const deliveryDateTime = deliveryTime === '—' ? deliveryDate : `${deliveryDate} - ${deliveryTime}`

  function photoSlot(id, base64) {
    const src = asDataUrl(base64, 'image/jpeg')
    if (src) {
      return `id="${id}" class="w-full h-[100px] rounded mb-2" style="overflow:hidden"><img src="${src}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;" />`
    }
    return `id="${id}" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span>`
  }

  const signatureSrc = asDataUrl(signature, 'image/png')
  const sigContent = signatureSrc
    ? `id="pod-sig" class="rounded h-[60px] bg-white mb-2" style="overflow:hidden"><img src="${signatureSrc}" style="width:100%;height:100%;object-fit:contain;" />`
    : `id="pod-sig" class="border-2 border-gray-400 rounded h-[60px] bg-white mb-2">`

  return {
    'CC-12345':                      order?.trackingCode || order?.tracking_code || order?.id || '—',
    'December 20, 2024 - 01:45 PM':  deliveryDateTime,
    'December 20, 2024':             deliveryDate,
    '01:45 PM':                      deliveryTime,
    'Sarah Khan | +91 98765 43210':  `${signedBy} | ${customerPhone}`,
    'Sarah Khan':                    signedBy,
    '+91 98765 43210':               customerPhone,
    'sarah.khan@email.com':          order?.customerEmail || order?.customer_email || user?.email || '—',
    '123 Oak Street, Whitefield':    order?.origin || order?.pickup || '—',
    'Bangalore, Karnataka - 560066': '',
    '456 Maple Avenue, Indiranagar': deliveryAddress,
    'Bangalore, Karnataka - 560038': '',
    'Prakash Reddy (DRV-8765)':      driverName,
    'Name: Sarah Khan':              `Name: ${signedBy}`,
    'id="pod-p1" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span>': photoSlot('pod-p1', photos[0]),
    'id="pod-p2" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span>': photoSlot('pod-p2', photos[1]),
    'id="pod-p3" class="w-full h-[100px] bg-gray-200 rounded flex items-center justify-center mb-2"><span class="text-[35px]">📷</span>': photoSlot('pod-p3', photos[2]),
    'id="pod-sig" class="border-2 border-gray-400 rounded h-[60px] bg-white mb-2">': sigContent,
  }
}

function instantQuotationReplacements(order, user) {
  const total = Number(order?.amount || order?.cost?.total || 0)
  return {
    'CC-12345':                      order?.id || 'QUOTE',
    'December 16, 2024':             order?.createdAt || order?.date || fmtShort(new Date()),
    'December 20, 2024':             order?.eta || 'TBD',
    'Sarah Khan':                    user?.name || '—',
    '+91 98765 43210':               user?.phone || '—',
    'sarah.khan@email.com':          user?.email || '—',
    '123 Oak Street, Whitefield':    order?.origin || order?.pickup || '—',
    'Bangalore, Karnataka - 560066': '',
    '456 Maple Avenue, Indiranagar': order?.destination || '—',
    'Bangalore, Karnataka - 560038': '',
    '₹4,500.00':  `₹${total.toFixed(2)}`,
    '₹4,500':     inr(total),
    '₹1,350':     inr(total),
    '₹3,150':     '₹0',
  }
}

function financeTransactionReplacements(record) {
  const metadata = record?.metadataJson || record?.metadata_json || {}
  const relatedOrder = record?.relatedOrder || record?.related_order || null
  const amount = Math.abs(Number(record?.amount || metadata?.amount || relatedOrder?.total_amount || 0))
  const rawDate = record?.transactionDate || record?.date || metadata?.requested_at || relatedOrder?.created_at || new Date()
  const parsedDate = new Date(rawDate)
  const formattedDate = Number.isNaN(parsedDate.getTime())
    ? String(rawDate || fmtShort(new Date()))
    : parsedDate.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  const formattedGeneratedAt = Number.isNaN(parsedDate.getTime())
    ? fmtShort(new Date())
    : parsedDate.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      })

  const direction = Number(record?.amount || 0) >= 0 ? 'Credit' : 'Debit'
  const slipTitle = record?.slipTitle || record?.typeLabel || record?.title || 'Finance Transaction Slip'
  const badge = record?.typeLabel || record?.type || 'Finance'
  const reference = record?.transactionCode || record?.transaction_code || record?.id || '—'
  const relatedRef = relatedOrder?.tracking_code
    || metadata?.tracking_code
    || metadata?.reference_code
    || '—'
  const beneficiary = record?.beneficiary
    || record?.name
    || metadata?.driver_name
    || relatedOrder?.customer_name
    || 'Cargo-Core Ledger'
  const paymentMethod = metadata?.payment_method
    || metadata?.collection_source
    || relatedOrder?.payment_mode
    || 'Internal Ledger'
  const notes = record?.notes
    || record?.desc
    || metadata?.notes
    || 'Auto-generated from Cargo-Core finance records.'

  return {
    '__SLIP_TITLE__': slipTitle,
    '__SLIP_BADGE__': badge,
    '__REFERENCE__': reference,
    '__DATE__': formattedDate,
    '__BENEFICIARY__': beneficiary,
    '__CATEGORY__': badge,
    '__DIRECTION__': direction,
    '__AMOUNT__': inr(amount),
    '__RELATED_REF__': relatedRef,
    '__PAYMENT_METHOD__': paymentMethod,
    '__DESCRIPTION__': record?.desc || notes,
    '__STATUS__': record?.status || 'Completed',
    '__NOTES__': notes,
    '__GENERATED_AT__': formattedGeneratedAt,
  }
}

function vehicleSafetyChecklistReplacements(driver, vehicle) {
  const now = new Date()
  const dateStr = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase()
  const vehicleReg = vehicle?.code || vehicle?.licensePlate || vehicle?.vehicle_number || driver?.vehicle || '—'
  const vehicleType = vehicle?.type || vehicle?.model || vehicle?.vehicleType || 'Truck'
  const driverName = driver?.name || '—'
  const driverId = driver?.id ? String(driver.id) : '—'
  const driverPhone = driver?.phone || '—'
  const location = driver?.location || driver?.current_location || '—'
  const tripId = driverId.slice(0, 6).toUpperCase()
  return {
    'TRP-7891':            `TRP-${tripId}`,
    'KA-51-MN-2347':       vehicleReg,
    'Dec 17, 2024':        dateStr,
    '06:30 AM':            timeStr,
    '24 ft Closed Body Truck': vehicleType,
    'Rajesh Kumar':        driverName,
    'KA-2019-0056789':     driverPhone || driverId,
    'Bangalore → Chennai': location,
    '347 km':              driver?.stops > 0 ? `${driver.stops * 15} km` : '—',
  }
}

function assetCheckoutReplacements(order, vehicle) {
  const vehicleReg = cleanText(vehicle?.code || vehicle?.licensePlate || vehicle?.vehicle_number || order?.vehicle)
  const vehicleType = cleanText(vehicle?.type || vehicle?.model || vehicle?.vehicleType || order?.vehicleType, 'Assigned vehicle')
  const driverName = cleanText(order?.driver || order?.name)
  const driverId = cleanText(order?.driverId || order?.id, '—')
  const shortDriverId = driverId === '—' ? '—' : driverId.slice(0, 8).toUpperCase()
  const driverPhone = cleanText(order?.driverPhone || order?.phone)
  const licenseNo = cleanText(order?.licenseNo || order?.license_number || order?.licenseNumber, shortDriverId !== '—' ? shortDriverId : 'To be assigned')
  const checkoutAt = order?.scheduledAt || order?.eta || order?.createdAt || new Date()
  const equipment = buildAssetEquipment(order)

  return {
    '__ORDER_OR_DRIVER_ID__': cleanText(order?.id || order?.trackingCode, shortDriverId),
    '__CHECKOUT_DATETIME__': `${fmtLong(checkoutAt)} - ${fmtTime(checkoutAt)}`,
    '__DRIVER_NAME__': driverName,
    '__DRIVER_CODE__': shortDriverId !== '—' ? `DRV-${shortDriverId}` : 'DRV-TBD',
    '__LICENSE_NO__': licenseNo,
    '__DRIVER_PHONE__': driverPhone,
    '__VEHICLE_NO__': vehicleReg,
    '__VEHICLE_TYPE__': vehicleType,
    '__ODOMETER__': cleanText(order?.odometerStart || order?.odometer || order?.odometerReading, 'To be logged at dispatch'),
    '__SUPERVISOR_NAME__': cleanText(order?.supervisorName, 'Dispatch Supervisor'),
    '__EQUIPMENT_JSON__': JSON.stringify(equipment),
  }
}

function tripManifestReplacements(manifest) {
  const manifestId = cleanText(manifest?.trackingCode || manifest?.tripId || manifest?.id)
  const orderId = cleanText(manifest?.orderId || manifest?.id, manifestId)
  const driverName = cleanText(manifest?.driver)
  const driverPhone = cleanText(manifest?.driver_phone || manifest?.driverPhone)
  const driverCodeSource = cleanText(manifest?.driverId || manifest?.id, 'TBD')
  const driverCode = driverCodeSource === '—' ? 'DRV-TBD' : `DRV-${driverCodeSource.slice(0, 6).toUpperCase()}`
  const vehicleCode = cleanText(manifest?.vehicle)
  const schedule = buildTripSchedule(manifest)
  const distanceValue = schedule.totalDistance
  const weightValue = `${num(manifest?.weight).toLocaleString('en-IN')} kg`
  const vehicleCapacity = vehicleCapacityLabel(manifest?.vehicleType || manifest?.vehicle, num(manifest?.weight))
  const fuelEstimate = schedule.fuelEstimate ? `${schedule.fuelEstimate} L` : 'TBD'
  const contactName = cleanText(manifest?.customerName, 'Customer Contact')
  const contactPhone = cleanText(manifest?.customerPhone, 'To be confirmed')

  return {
    '__TRIP_ID__': manifestId,
    '__ORDER_ID__': orderId,
    '__TRIP_DATE__': fmtLong(manifest?.scheduledAt || manifest?.eta || manifest?.createdAt || new Date()),
    '__DRIVER_NAME__': driverName,
    '__DRIVER_CODE__': driverCode,
    '__LICENSE_NO__': cleanText(manifest?.licenseNo, driverCodeSource),
    '__DRIVER_PHONE__': driverPhone,
    '__VEHICLE_NO__': vehicleCode,
    '__VEHICLE_TYPE__': cleanText(manifest?.vehicleType || manifest?.vehicle, 'Assigned vehicle'),
    '__VEHICLE_CAPACITY__': vehicleCapacity,
    '__FUEL_START__': cleanText(manifest?.fuelStart, 'To be logged at dispatch'),
    '__ROUTE_TITLE__': `GPS Route: ${routeLabel(manifest?.pickupAddr)} → ${routeLabel(manifest?.deliveryAddr)}`,
    '__ROUTE_META__': schedule.routeMeta,
    '__ROUTE_VIA__': routeViaLabel(manifest, vehicleCode),
    '__PICKUP_ADDR__': compactAddress(manifest?.pickupAddr),
    '__PICKUP_TIME__': schedule.pickupTime,
    '__CONTACT_NAME__': contactName,
    '__CONTACT_PHONE__': contactPhone,
    '__LOAD_TIME__': schedule.loadTime,
    '__DELIVERY_ADDR__': compactAddress(manifest?.deliveryAddr),
    '__DELIVERY_TIME__': schedule.deliveryTime,
    '__UNLOAD_TIME__': schedule.unloadTime,
    '__RETURN_DEPOT__': compactAddress(manifest?.warehouse || manifest?.pickupAddr, 'CargoCore Dispatch Hub'),
    '__RETURN_TIME__': schedule.returnTime,
    '__TOTAL_DISTANCE__': distanceValue,
    '__EST_DURATION__': schedule.totalDuration,
    '__FUEL_ESTIMATE__': fuelEstimate,
    '__TOTAL_STOPS__': String(Math.max(3, num(manifest?.stopCount, 2) || 3)),
    '__TOTAL_BOXES__': `${estimateBoxes(manifest)} boxes`,
    '__EST_WEIGHT__': weightValue,
    '__SPECIAL_ITEMS__': summarizeSpecialItems(manifest),
    '__TRIP_NOTES__': cleanText(manifest?.specialInstructions || manifest?.notes, 'Dispatch slip generated from the selected trip/order details.'),
  }
}

function digitalPickListReplacements(data) {
  const { wave, items = [], waves = [] } = data || {}
  const now = new Date()
  const pickDate = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })

  // ── master view: top-level button passes { waves } with no wave-level items ──
  if (!wave) {
    const totalOrders = waves.length
    const totalItems  = waves.reduce((s, w) => s + (Number(w.items) || 0), 0)

    const rows = waves.map((w, idx) => {
      const bg     = idx % 2 === 0 ? 'bg-blue-50' : idx % 2 === 1 ? 'bg-gray-50' : ''
      const status = (w.status || '—').replace(/_/g, ' ')
      return `<tr class="${bg}">
        <td class="text-center p-2 border border-gray-300"><input type="checkbox"></td>
        <td class="p-2 border border-gray-300 font-semibold">${w.id || '—'}</td>
        <td class="text-center p-2 border border-gray-300">${w.priority || 'STANDARD'}</td>
        <td class="text-center p-2 border border-gray-300 font-semibold">${w.items || 0}</td>
        <td class="text-center p-2 border border-gray-300">${status}</td>
      </tr>`
    }).join('\n')

    const activePickers = [...new Set(
      waves.flatMap(w => (w.laborAssigned || []).map(l => l.name).filter(Boolean))
    )]
    const pickerInfo = activePickers.length
      ? activePickers.join(', ')
      : waves.some(w => w.assignedPicker)
        ? waves.map(w => w.assignedPicker).filter(Boolean).join(', ')
        : 'Unassigned'

    return {
      '__ORDER_ID__':      'ALL ORDERS',
      '__PICK_DATE__':     pickDate,
      '__MOVE_DATE__':     pickDate,
      '__PRIORITY__':      `${totalOrders} ORDERS`,
      '__PICKER_INFO__':   pickerInfo,
      '__WALKING_PATH__':  '<span class="bg-blue-600 text-white px-2 py-1 rounded font-semibold">START</span><span>→</span><span class="bg-white px-2 py-1 rounded border border-blue-300">All Zones</span><span>→</span><span class="bg-green-600 text-white px-2 py-1 rounded font-semibold">LOADING DOCK</span>',
      '__PATH_SUMMARY__':  `${totalOrders} active orders`,
      '__ITEMS_HEADING__': `ACTIVE PICK WAVES (${totalOrders} ORDERS)`,
      // Replace the column headers to fit wave-level data
      '>Item Description<': '>Order ID / Type<',
      '>Location<':         '>Priority<',
      '>Qty<':              '>Items<',
      '>Bin/Rack<':         '>Status<',
      '__ITEMS_ROWS__':    rows || '<tr><td colspan="5" class="text-center p-4 text-gray-400">No active pick waves at this time</td></tr>',
      '__TOTAL_ITEMS__':   String(totalOrders),
      '__TOTAL_QTY__':     String(totalItems),
      '__TOTAL_AISLES__':  '—',
      '__EST_TIME__':      '—',
    }
  }

  // ── single-wave detailed pick list ──────────────────────────────────────────
  const orderId   = wave?.id || '—'
  const deadline  = wave?.deadline || pickDate
  const priority  = (wave?.priority || 'STANDARD').toUpperCase()
  const pickers   = (wave?.laborAssigned || []).map(l => l.name).filter(Boolean).join(', ')
    || wave?.assignedPicker || 'Unassigned'

  // Build unique aisles from items — backend gives item.aisle directly from InventoryItem
  const aisleSet = new Set()
  items.forEach(item => {
    if (item.aisle) aisleSet.add(String(item.aisle))
  })
  const aisles      = aisleSet.size ? [...aisleSet].sort() : []
  const totalAisles = aisles.length || '—'

  // Walking path HTML using real aisle labels from inventory
  let pathHtml = '<span class="bg-blue-600 text-white px-2 py-1 rounded font-semibold">START</span>'
  for (const aisle of aisles) {
    pathHtml += `<span>→</span><span class="bg-white px-2 py-1 rounded border border-blue-300">Aisle ${aisle}</span>`
  }
  pathHtml += '<span>→</span><span class="bg-green-600 text-white px-2 py-1 rounded font-semibold">LOADING DOCK</span>'

  // Estimated time: ~3 min per item pick + 5 min transit between aisles
  const estMinutes = Math.max(10, items.length * 3 + aisles.length * 5)
  const estTime    = estMinutes >= 60
    ? `${Math.floor(estMinutes / 60)}h ${estMinutes % 60}m`
    : `${estMinutes} min`

  const totalQty = items.reduce((s, it) => s + Number(it.quantity_required || it.required_quantity || it.quantity || 0), 0)

  // Build item rows — clean guide for the picker to carry around the warehouse
  const rows = items.map((item, idx) => {
    const shortage    = Number(item.shortage_quantity || 0)
    const qtyRequired = Number(item.quantity_required || item.required_quantity || item.quantity || 0)

    // Alternating row shading; red tint if stock is short
    const bg = shortage > 0 ? '#fff5f5' : idx % 2 === 0 ? '#f0f7ff' : '#ffffff'

    // Item name — prefer display name, fallback to SKU trimmed for readability
    const rawName = item.item_name || item.name || ''
    const sku     = item.sku || '—'
    const name    = rawName && rawName !== sku ? rawName : `Item ${idx + 1}`

    // Location: aisle + section
    const locationParts = []
    if (item.aisle)              locationParts.push(`Aisle ${item.aisle}`)
    if (item.section)            locationParts.push(`Sec ${item.section}`)
    if (item.zone && !item.aisle) locationParts.push(`Zone ${item.zone}`)
    const location = locationParts.length
      ? locationParts.join(' / ')
      : (item.location_path && item.location_path !== 'Location not mapped' ? item.location_path : '—')

    // Bin / Rack
    const binParts = []
    if (item.rack) binParts.push(item.rack)
    if (item.cell) binParts.push(item.cell)
    if (!binParts.length) {
      if (item.shelf) binParts.push(`S${item.shelf}`)
      if (item.bin)   binParts.push(`B${item.bin}`)
    }
    const binLabel = binParts.length ? binParts.join('-') : '—'

    // Scan code for barcode scanning
    const scanCode = item.scan_code || item.sku || '—'

    // Shortage warning — tells picker to check with supervisor
    const shortageBadge = shortage > 0
      ? `<div style="color:#dc2626;font-size:8px;font-weight:bold;margin-top:2px;">⚠ Only ${qtyRequired - shortage} in stock — check supervisor</div>`
      : ''

    return `<tr style="background:${bg};">
      <td style="text-align:center;padding:8px 4px;border:1px solid #d1d5db;">
        <span class="check-box"></span>
      </td>
      <td style="padding:8px;border:1px solid #d1d5db;">
        <span style="font-weight:600;font-size:10px;">${name}</span>
        <span style="color:#9ca3af;font-size:8px;display:block;margin-top:1px;">${sku}</span>
        ${shortageBadge}
      </td>
      <td style="text-align:center;padding:8px 4px;border:1px solid #d1d5db;font-size:9px;">${location}</td>
      <td style="text-align:center;padding:8px 4px;border:1px solid #d1d5db;font-size:13px;font-weight:bold;">${qtyRequired}</td>
      <td style="text-align:center;padding:8px 4px;border:1px solid #d1d5db;font-size:9px;font-family:monospace;">${binLabel}</td>
      <td style="text-align:center;padding:8px 4px;border:1px solid #d1d5db;font-size:8px;color:#6b7280;word-break:break-all;">${scanCode}</td>
    </tr>`
  }).join('\n')

  return {
    '__ORDER_ID__':      orderId,
    '__PICK_DATE__':     pickDate,
    '__MOVE_DATE__':     deadline,
    '__PRIORITY__':      priority,
    '__PICKER_INFO__':   pickers,
    '__WALKING_PATH__':  pathHtml,
    '__PATH_SUMMARY__':  aisles.length
      ? `Estimated time: ${estTime} | Aisles to visit: ${aisles.join(' → ')}`
      : `Estimated time: ${estTime}`,
    '__ITEMS_HEADING__': `Items to Pick — ${items.length} item${items.length !== 1 ? 's' : ''}, ${totalQty} pcs total`,
    '__ITEMS_ROWS__':    rows || '<tr><td colspan="6" style="text-align:center;padding:16px;color:#9ca3af;">No items found for this order</td></tr>',
    '__TOTAL_ITEMS__':   String(items.length),
    '__TOTAL_QTY__':     String(totalQty),
    '__TOTAL_AISLES__':  String(totalAisles),
    '__EST_TIME__':      estTime,
  }
}

function getReplacements(key, order, user) {
  switch (key) {
    case 'bookingConfirmation':    return bookingConfirmationReplacements(order, user)
    case 'finalTaxInvoice':        return finalTaxInvoiceReplacements(order, user)
    case 'proofOfDelivery':        return proofOfDeliveryReplacements(order, user)
    case 'instantQuotation':       return instantQuotationReplacements(order, user)
    case 'financeTransaction':     return financeTransactionReplacements(order)
    case 'vehicleSafetyChecklist': return vehicleSafetyChecklistReplacements(order, user)
    case 'assetCheckout':          return assetCheckoutReplacements(order, user)
    case 'tripManifest':           return tripManifestReplacements(order)
    case 'digitalPickList':        return digitalPickListReplacements(order)
    default:                       return {}
  }
}

// ─── public composable ────────────────────────────────────────────────────────

export function useSlipPrinter() {
  /**
   * Pre-fetch slip HTML into cache so subsequent opens are synchronous.
   * Call this in onMounted for slips you know you'll need.
   */
  async function prefetchSlips(keys) {
    await Promise.all(keys.map(k => fetchSlipHtml(k)))
  }

  /** Open slip with no data substitution (static preview) */
  async function openSlip(key) {
    const cached = _htmlCache.has(key)
    const pendingWindow = cached ? null : window.open('', '_blank')
    const html = cached ? _htmlCache.get(key) : await fetchSlipHtml(key)
    if (!html) {
      if (pendingWindow && !pendingWindow.closed) pendingWindow.close()
      return false
    }
    openBlobHtml(fixAssetPaths(html), pendingWindow)
    return true
  }

  /**
   * Open slip with real data injected.
   * If HTML is already in cache this is fully synchronous — no popup blocker.
   * @param {string} key   - slip key e.g. 'bookingConfirmation'
   * @param {object} order - shipment/order object from vendor store
   * @param {object} user  - current user { name, email, phone }
   */
  async function openSlipWithData(key, order, user = {}) {
    const cached = _htmlCache.has(key)
    const pendingWindow = cached ? null : window.open('', '_blank')
    const html = cached ? _htmlCache.get(key) : await fetchSlipHtml(key)
    if (!html) {
      if (pendingWindow && !pendingWindow.closed) pendingWindow.close()
      return false
    }
    const replacements = getReplacements(key, order, user)
    openBlobHtml(applyReplacements(fixAssetPaths(html), replacements), pendingWindow)
    return true
  }

  return { openSlip, openSlipWithData, prefetchSlips, SLIP_LABELS, SLIP_ICONS }
}
