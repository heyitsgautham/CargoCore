import { describe, expect, it } from 'vitest'
import {
  CSV_TEMPLATES,
  computeQuote,
  filterMyShipments,
  validateShipmentForm,
} from '@/IV-views/Vendor/createShipment/shipmentForm'

const base = {
  category: 'commercial',
  weight: 100,
  palletCount: 1,
  pickupType: 'hub',
  priority: 'Standard',
  laborRequired: false,
  laborCount: 1,
  packingRequired: false,
  insuranceRequired: 'no',
  declaredValue: 0,
}

describe('vendor shipment quote', () => {
  it('charges the minimum for a short, light standard booking', () => {
    expect(computeQuote(base, {}, null)).toEqual({
      baseTransport: 500,
      laborCharges: 0,
      packingFee: 0,
      insurance: 0,
      distanceKm: 0,
      total: 500,
    })
  })

  it('adds distance, pallets, doorstep pickup and the express multiplier', () => {
    const quote = computeQuote(
      {
        ...base,
        category: 'palletized',
        palletCount: 10,
        pickupType: 'doorstep',
        priority: 'Express',
      },
      { baseBookingFee: 220, perKmRate: 12, expressMultiplier: 1.5, minimumCharge: 500 },
      100,
    )
    // (220 + 50 + 1200 + 150 + 150) * 1.5
    expect(quote.baseTransport).toBe(2655)
    expect(quote.total).toBe(2655)
  })

  it('adds labour, packing and insurance on the declared value', () => {
    const quote = computeQuote(
      {
        ...base,
        laborRequired: true,
        laborCount: 2,
        packingRequired: true,
        insuranceRequired: 'yes',
        declaredValue: 10000,
      },
      { customerLaborRate: 250, customerPackingFee: 200, insurancePct: 3 },
      0,
    )
    expect(quote).toMatchObject({ laborCharges: 500, packingFee: 200, insurance: 300, total: 1500 })
  })
})

describe('vendor shipment validation', () => {
  it('lists every missing field for an empty commercial booking', () => {
    expect(validateShipmentForm({ ...base, weight: 0 })).toEqual([
      'Goods description required',
      'Pickup hub required',
      'Weight required',
      'Destination required',
      'Destination city required',
      'Pincode required',
      'Pickup date required',
    ])
  })

  it('asks for customer details on B2C and the pickup address on doorstep pickups', () => {
    const errors = validateShipmentForm({
      ...base,
      category: 'b2c',
      pickupType: 'doorstep',
      description: 'TV',
      destination: 'x',
      destinationCity: 'y',
      pincode: '560001',
      pickupDate: '2026-11-01',
    })
    expect(errors).toEqual([
      'Customer name required',
      'Customer phone required',
      'Pickup address required',
      'Pickup city required',
      'Pickup pincode required',
    ])
  })
})

describe('my shipments and templates', () => {
  it('filters shipments by status and text', () => {
    const shipments = [
      { id: 'QC-1', statusKey: 'pending', destination: 'Mumbai', description: 'Laptops' },
      { id: 'QC-2', statusKey: 'delivered', destination: 'Pune', description: null },
    ]
    expect(filterMyShipments(shipments, 'delivered', '').map((s) => s.id)).toEqual(['QC-2'])
    expect(filterMyShipments(shipments, 'all', 'laptop').map((s) => s.id)).toEqual(['QC-1'])
  })

  it('ships a template with a header and two sample rows per category', () => {
    for (const template of Object.values(CSV_TEMPLATES)) {
      expect(template.filename.endsWith('.csv')).toBe(true)
      expect(template.rows).toHaveLength(3)
      const columns = template.rows[0].split(',').length
      expect(template.rows.every((row) => row.split(',').length === columns)).toBe(true)
    }
  })
})
