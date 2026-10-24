/**
 * useSlipPrinter — opens CargoCore HTML slips with real data injected.
 * Fetches HTML at runtime from /html-slips/ (served by Vite plugin).
 */

import {
  bookingConfirmationReplacements,
  finalTaxInvoiceReplacements,
  proofOfDeliveryReplacements,
  instantQuotationReplacements,
} from './slips/orderSlips'
import {
  financeTransactionReplacements,
  vehicleSafetyChecklistReplacements,
  assetCheckoutReplacements,
  tripManifestReplacements,
  digitalPickListReplacements,
  laborAssignmentReplacements,
} from './slips/operationsSlips'

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

function openBlobHtml(html, targetWindow = null, autoPrint = false) {
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
    const url = `/slip-preview?k=${key}${autoPrint ? '&print=1' : ''}`
    if (targetWindow && !targetWindow.closed) {
      targetWindow.location.href = url
      return
    }
    window.open(url, '_blank')
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

// ─── per-slip replacement maps live in ./slips/ ───────────────────────────────

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
    case 'laborAssignment':        return laborAssignmentReplacements(order)
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

  async function printSlipWithData(key, order, user = {}) {
    const cached = _htmlCache.has(key)
    const pendingWindow = cached ? null : window.open('', '_blank')
    const html = cached ? _htmlCache.get(key) : await fetchSlipHtml(key)
    if (!html) {
      if (pendingWindow && !pendingWindow.closed) pendingWindow.close()
      return false
    }
    const replacements = getReplacements(key, order, user)
    openBlobHtml(applyReplacements(fixAssetPaths(html), replacements), pendingWindow, true)
    return true
  }

  return { openSlip, openSlipWithData, printSlipWithData, prefetchSlips, SLIP_LABELS, SLIP_ICONS }
}
