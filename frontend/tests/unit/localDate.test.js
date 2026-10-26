import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { localDateISO } from '@/utils/date'
import { todayDate } from '@/components/meetingScheduler/meetingFormat'

const originalTz = process.env.TZ

describe('dates in the user time zone', () => {
  beforeAll(() => {
    process.env.TZ = 'Asia/Kolkata'
  })
  afterAll(() => {
    process.env.TZ = originalTz
  })
  afterEach(() => vi.useRealTimers())

  it('formats local midnight as that day, not the UTC day before', () => {
    expect(localDateISO(new Date(2026, 0, 1))).toBe('2026-01-01')
    expect(localDateISO(new Date(2026, 9, 27, 23, 59))).toBe('2026-10-27')
  })

  it('defaults a new meeting to the local day at 1 AM in India', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-27T01:00:00+05:30'))
    expect(todayDate()).toBe('2026-10-27')
  })
})
