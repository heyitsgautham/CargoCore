/**
 * Placeholder values for customer-facing slips: booking confirmation, tax invoice, proof of delivery and quotation.
 */

import { buildPodData } from '@/utils/pod'
import {
  inr,
  fmtShort,
  num,
  cleanText,
  escapeHtml,
} from './formatters'

export function bookingConfirmationReplacements(order, user) {
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

export function finalTaxInvoiceReplacements(order, user) {
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

export function podMetricLabel(value, suffix = '', fallback = 'Not specified') {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback
  return `${parsed.toLocaleString('en-IN')}${suffix}`
}

export function buildPodSummarySection(order, pod) {
  const summaryCards = [
    {
      label: 'Cargo Type',
      value: cleanText(order?.description || order?.category || order?.cargoType || order?.cargo_type, 'Standard shipment'),
    },
    {
      label: 'Declared Weight',
      value: podMetricLabel(order?.weight || order?.cargo_weight_kg, ' kg'),
    },
    {
      label: 'Volume',
      value: podMetricLabel(order?.volume || order?.cargo_volume_m3, ' m3'),
    },
    {
      label: 'Pallets',
      value: podMetricLabel(order?.pallets || order?.palletCount, '', 'Not used'),
    },
    {
      label: 'Handling Mode',
      value: order?.packingRequired
        ? 'Packed shipment with material handling'
        : 'Direct shipment with no packing service booked',
    },
    {
      label: 'Delivery Status',
      value: pod?.confirmed === false ? 'Pending confirmation' : 'Delivered and acknowledged',
    },
  ]

  const cardsMarkup = summaryCards.map((card) => `
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <p class="text-[9px] font-bold text-gray-500 uppercase tracking-wide mb-1">${escapeHtml(card.label)}</p>
              <p class="text-[11px] font-semibold text-gray-900">${escapeHtml(card.value)}</p>
            </div>
  `).join('')

  return `
        <div>
          <h3 class="text-[13px] font-bold text-gray-800 mb-3 pb-2 border-b border-gray-300">DELIVERY SUMMARY</h3>
          <div class="grid grid-cols-2 gap-3">
            ${cardsMarkup}
          </div>
        </div>
  `
}

export function buildPodServicesSection(order, pod) {
  const photoCount = Number(pod?.photoCount || pod?.photos?.length || 0)
  const laborCount = Math.max(0, num(order?.laborCount || order?.labor_count))
  const services = [
    {
      title: 'Final Delivery Handover',
      description: 'Shipment reached the destination and was acknowledged by the receiver.',
    },
    {
      title: 'Proof of Delivery Capture',
      description: pod?.signatureCaptured || photoCount > 0
        ? `Delivery record captured with ${photoCount || 0} photo${photoCount === 1 ? '' : 's'} and recipient confirmation.`
        : 'Delivery confirmation was recorded for this shipment.',
    },
  ]

  if (laborCount > 0) {
    services.push({
      title: 'Loading and Unloading Support',
      description: `${laborCount} crew member${laborCount === 1 ? '' : 's'} assisted with cargo handling.`,
    })
  }

  if (order?.packingRequired) {
    services.push({
      title: 'Protective Packing Service',
      description: 'Packing materials and protective handling were included for this order.',
    })
  } else {
    services.push({
      title: 'Non-Packing Shipment',
      description: 'No packing or unpacking service was booked for this order.',
    })
  }

  const cardsMarkup = services.map((service) => `
            <div class="flex items-center gap-2 bg-green-50 p-3 rounded border border-green-200">
              <div class="text-green-600 text-[20px]">&#10003;</div>
              <div>
                <p class="text-[11px] font-semibold text-gray-900">${escapeHtml(service.title)}</p>
                <p class="text-[9px] text-gray-600">${escapeHtml(service.description)}</p>
              </div>
            </div>
  `).join('')

  return `
        <div>
          <h3 class="text-[13px] font-bold text-gray-800 mb-3 pb-2 border-b border-gray-300">SERVICES COMPLETED</h3>
          <div class="grid grid-cols-2 gap-3">
            ${cardsMarkup}
          </div>
        </div>
  `
}

export function buildPodFeedbackSection(order) {
  const rating = Number(order?.customerRating ?? order?.customer_rating)
  const hasRating = Number.isFinite(rating) && rating > 0
  const feedback = cleanText(order?.customerFeedback || order?.customer_feedback, '')

  if (!hasRating) {
    return `
        <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h3 class="text-[11px] font-bold text-blue-900 mb-2">DELIVERY FEEDBACK</h3>
          <div class="bg-white p-3 rounded border border-blue-200">
            <p class="text-[10px] text-gray-600">No delivery rating or written feedback has been submitted yet.</p>
          </div>
        </div>
    `
  }

  const stars = Array.from({ length: 5 }, (_, index) => (
    `<span class="text-[18px] ${index < rating ? 'text-yellow-500' : 'text-gray-300'}">${index < rating ? '&#9733;' : '&#9734;'}</span>`
  )).join('')

  return `
        <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h3 class="text-[11px] font-bold text-blue-900 mb-2">DELIVERY FEEDBACK</h3>
          <div class="bg-white p-3 rounded border border-blue-200">
            <div class="flex gap-1 mb-2 items-center">
              ${stars}
              <span class="text-[11px] font-semibold text-gray-700 ml-2">${rating.toFixed(1)} / 5.0</span>
            </div>
            <p class="text-[10px] text-gray-700 italic">${feedback ? `"${escapeHtml(feedback)}"` : 'Rated delivery with no written feedback.'}</p>
          </div>
        </div>
  `
}

export function proofOfDeliveryReplacements(order, user) {
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
    '__POD_DELIVERY_SUMMARY__':      buildPodSummarySection(order, pod),
    '__POD_SERVICES_COMPLETED__':    buildPodServicesSection(order, pod),
    '__POD_CUSTOMER_FEEDBACK__':     buildPodFeedbackSection(order),
  }
}

export function instantQuotationReplacements(order, user) {
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
