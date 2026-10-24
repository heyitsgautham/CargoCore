import { describe, expect, it } from 'vitest'
import { buildPodData, getPodPhotos, getPodSignature, parsePodDeliveryNotes } from '@/utils/pod'

describe('parsePodDeliveryNotes', () => {
  it('pulls the recipient name out of a "Delivered to" line', () => {
    const parsed = parsePodDeliveryNotes('Delivered to: Asha Rao\nLeft at the front desk')
    expect(parsed).toEqual({ recipientName: 'Asha Rao', notes: 'Left at the front desk' })
  })

  it('accepts the "Signed off by" and "Recipient" spellings, case-insensitively', () => {
    expect(parsePodDeliveryNotes('signed off by: Ravi').recipientName).toBe('Ravi')
    expect(parsePodDeliveryNotes('RECIPIENT: Meena').recipientName).toBe('Meena')
  })

  it('trims blank lines and handles Windows line endings', () => {
    const parsed = parsePodDeliveryNotes('  first  \r\n\r\n second ')
    expect(parsed).toEqual({ recipientName: null, notes: 'first\nsecond' })
  })

  it('returns nulls for empty input', () => {
    expect(parsePodDeliveryNotes(undefined)).toEqual({ recipientName: null, notes: null })
  })
})

describe('getPodPhotos', () => {
  it('prefers the pod.photos array and drops empty entries', () => {
    expect(getPodPhotos({ pod: { photos: ['a.jpg', '', null, 'b.jpg'] } })).toEqual([
      'a.jpg',
      'b.jpg',
    ])
  })

  it('falls back to a single pod.photo, then to pod_photos', () => {
    expect(getPodPhotos({ pod: { photo: 'one.jpg' } })).toEqual(['one.jpg'])
    expect(getPodPhotos({ pod_photos: ['x.jpg', null] })).toEqual(['x.jpg'])
  })

  it('returns an empty list when the order has no photos', () => {
    expect(getPodPhotos({})).toEqual([])
    expect(getPodPhotos(null)).toEqual([])
  })
})

describe('getPodSignature', () => {
  it('checks pod.signature, then poc_signature, then pod_signature', () => {
    expect(getPodSignature({ pod: { signature: 's1' }, poc_signature: 's2' })).toBe('s1')
    expect(getPodSignature({ poc_signature: 's2', pod_signature: 's3' })).toBe('s2')
    expect(getPodSignature({ pod_signature: 's3' })).toBe('s3')
    expect(getPodSignature({})).toBeNull()
  })
})

describe('buildPodData', () => {
  it('builds proof-of-delivery data from the raw backend order fields', () => {
    const pod = buildPodData({
      pod_photos: ['p1.jpg', 'p2.jpg'],
      pod_signature: 'sig.png',
      delivery_notes: 'Delivered to: Kiran\nFragile items checked',
    })

    expect(pod).toMatchObject({
      photo: 'p1.jpg',
      photoCount: 2,
      signature: 'sig.png',
      signatureCaptured: true,
      signedBy: 'Kiran',
      recipient: 'Kiran',
      notes: 'Fragile items checked',
      timestamp: 'Delivered',
      location: '—',
      confirmed: true,
    })
  })

  it('lets explicit pod fields win over parsed notes', () => {
    const pod = buildPodData({
      pod: {
        signedBy: 'Gate guard',
        time: '10:30',
        location: 'Dock 2',
        confirmed: false,
        notes: 'raw',
      },
      customer_name: 'Customer',
    })

    expect(pod.signedBy).toBe('Gate guard')
    expect(pod.time).toBe('10:30')
    expect(pod.location).toBe('Dock 2')
    expect(pod.confirmed).toBe(false)
    expect(pod.notes).toBe('raw')
  })

  it('falls back to the customer name and then to the supplied default', () => {
    expect(buildPodData({ customerName: 'Lata' }).signedBy).toBe('Lata')
    expect(buildPodData({}, { signedByFallback: 'Front desk' }).signedBy).toBe('Front desk')
    expect(buildPodData({}).signatureCaptured).toBe(false)
  })
})
