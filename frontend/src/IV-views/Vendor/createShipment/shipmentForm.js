// Pricing, validation and list filtering for the vendor's create shipment page.

/**
 * The live quote for a booking: base fee plus weight and road distance, pallet and
 * doorstep pickup surcharges, the priority multiplier, then labour, packing and insurance.
 */
export function computeQuote(form, rates, distanceKm) {
    const r = rates || {}
    const km = distanceKm || 0
    const distCharge = Math.round(km * (r.perKmRate ?? 12))
    let base = (r.baseBookingFee ?? 220) + (form.weight || 0) * 0.5 + distCharge
    if (form.category === 'palletized') base += (form.palletCount || 0) * 15
    if (form.pickupType === 'doorstep') base += 150
    if (form.priority === 'Express') base *= (r.expressMultiplier ?? 1.5)
    else if (form.priority === 'Urgent') base *= (r.dynamic?.emergency ?? r.expressMultiplier ?? 1.5)
    base = Math.max(base, r.minimumCharge ?? 500)
    const labor = form.laborRequired ? form.laborCount * (r.customerLaborRate ?? 250) : 0
    const packing = form.packingRequired ? (r.customerPackingFee ?? 200) : 0
    const insurance = form.insuranceRequired === 'yes' && form.declaredValue ? (form.declaredValue * ((r.insurancePct ?? 3) / 100)) : 0
    return {
        baseTransport: Math.round(base),
        laborCharges: labor,
        packingFee: packing,
        insurance: Math.round(insurance),
        distanceKm: km,
        total: Math.round(base + labor + packing + insurance),
    }
}

/** Messages for every required field the form still misses, in display order. */
export function validateShipmentForm(form) {
    const e = []
    if (!form.description) e.push('Goods description required')
    if (form.category === 'palletized' && (!form.palletCount || form.palletCount < 1)) e.push('Pallet count required')
    if (form.category === 'b2c') {
        if (!form.customerName) e.push('Customer name required')
        if (!form.customerPhone) e.push('Customer phone required')
    }
    if (form.pickupType === 'doorstep') {
        if (!form.pickupAddress) e.push('Pickup address required')
        if (!form.pickupCity) e.push('Pickup city required')
        if (!form.pickupPincode) e.push('Pickup pincode required')
    }
    if (form.pickupType === 'hub' && !form.pickupHub) e.push('Pickup hub required')
    if (!form.weight || form.weight < 1) e.push('Weight required')
    if (!form.destination) e.push('Destination required')
    if (!form.destinationCity) e.push('Destination city required')
    if (!form.pincode) e.push('Pincode required')
    if (!form.pickupDate) e.push('Pickup date required')
    return e
}

export function filterMyShipments(shipments, statusFilter, query) {
    let list = shipments
    if (statusFilter !== 'all') list = list.filter(s => s.statusKey === statusFilter)
    if (query.trim()) {
        const q = query.toLowerCase()
        list = list.filter(s => s.id.toLowerCase().includes(q) || s.destination.toLowerCase().includes(q) || (s.description || '').toLowerCase().includes(q))
    }
    return list
}

export const CSV_TEMPLATES = {
    commercial: {
        filename: 'commercial_b2b_template.csv',
        rows: [
            'reference_id,pickup_address,delivery_address,cargo_type,weight_kg,pallets,declared_value,payment_mode',
            'ORD-001,Mumbai Warehouse MIDC Andheri,Delhi Central Hub Okhla,Electronics,500,5,50000,Invoice',
            'ORD-002,Pune Factory Pimpri,Bangalore Depot Whitefield,Machinery,1200,12,120000,Prepaid',
        ]
    },
    palletized: {
        filename: 'palletized_template.csv',
        rows: [
            'reference_id,pickup_address,delivery_address,pallets,weight_kg,pallet_type,declared_value,payment_mode',
            'ORD-001,Pune Factory Pimpri,Bangalore Depot Whitefield,10,2000,Standard EUR,100000,Invoice',
            'ORD-002,Chennai Port Trust,Hyderabad JNPC Hub,4,800,Heat-Treated,40000,Prepaid',
        ]
    },
    b2c: {
        filename: 'b2c_shipment_template.csv',
        rows: [
            'reference_id,customer_name,customer_phone,pickup_address,delivery_address,item_description,weight_kg,declared_value',
            'ORD-001,Rahul Sharma,9876543210,Seller Hub Mumbai,123 Main St Bangalore,Smart TV 55 inch,12,25000',
            'ORD-002,Priya Patel,9123456789,Retail Store Ahmedabad,Plot 45 Surat,Home Appliances Set,35,15000',
        ]
    }
}

export function downloadTemplate(category) {
    const t = CSV_TEMPLATES[category]
    if (!t) return
    const blob = new Blob([t.rows.join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = t.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}
