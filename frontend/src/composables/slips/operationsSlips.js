/**
 * Placeholder values for operations slips: finance transaction, safety checklist, asset checkout, trip manifest, pick list and labour assignment.
 */

import {
  inr,
  fmtShort,
  fmtLong,
  fmtTime,
  num,
  cleanText,
  compactAddress,
  routeLabel,
  vehicleCapacityLabel,
  estimateBoxes,
  summarizeSpecialItems,
  routeViaLabel,
  buildTripSchedule,
  buildAssetEquipment,
} from './formatters'

export function financeTransactionReplacements(record) {
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

export function vehicleSafetyChecklistReplacements(driver, vehicle) {
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

export function assetCheckoutReplacements(order, vehicle) {
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

export function tripManifestReplacements(manifest) {
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

export function digitalPickListReplacements(data) {
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

export function laborAssignmentReplacements(staff) {
  const now = new Date()
  const dateStr = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })
  const shortId = staff?.id ? String(staff.id).slice(0, 6).toUpperCase() : 'TBD'
  const empCode = `EMP-${shortId}`
  const staffName = cleanText(staff?.name, 'Staff Member')
  const orderId = cleanText(staff?.orderId, '—')
  const startTime = (staff?.startTime && staff.startTime !== '--') ? staff.startTime : '09:00 AM'
  const role = cleanText(staff?.role, 'Labourer')
  const task = cleanText(staff?.task, 'Assigned Task')
  const perf = staff?.perf != null ? `${staff.perf}%` : '—'

  return {
    'CC-12345':                        orderId,
    'December 20, 2024':               dateStr,
    '09:00 AM - 05:00 PM':             `${startTime} — End of Shift`,
    'Sarah Khan | +91 98765 43210':    staffName,
    'Rajesh Kumar':                    staffName,
    'EMP-2541':                        empCode,
    'TEAM LEAD':                       role.toUpperCase(),
    'ASSIGNED WORKERS (4 MEMBERS)':    'ASSIGNED WORKER',
    'Vijay Sharma':                    '—',
    'Arun Patel':                      '—',
    'Mohammed Rafi':                   '—',
    'EMP-3782':                        '—',
    'EMP-4156':                        '—',
    'EMP-5234':                        '—',
    '8 Years':                         perf,
    'Supervise team, coordinate with customer, ensure quality control': task,
    '123 Oak Street, Whitefield':      'Warehouse',
    'Bangalore - 560066':              '',
    '456 Maple Avenue, Indiranagar':   orderId !== '—' ? `Order: ${orderId}` : 'Order Location',
    'Bangalore - 560038':              '',
    'Customer has antique furniture - handle with extra care':          'Follow warehouse safety guidelines',
    '2nd floor delivery - ensure lift is operational':                  'Coordinate with warehouse supervisor',
  }
}
