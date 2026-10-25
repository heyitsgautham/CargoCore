import { describe, expect, it } from 'vitest'
import { paddedCornerPairs, validPoints } from '@/utils/mapBounds'

describe('validPoints', () => {
  it('keeps numeric pairs, converts numeric strings and drops missing coordinates', () => {
    expect(
      validPoints([
        [12.9, 77.5],
        ['13.0', '77.6'],
        [null, 77.1],
        [12.1, undefined],
        ['', 1],
        [NaN, 2],
      ]),
    ).toEqual([
      [12.9, 77.5],
      [13, 77.6],
    ])
    expect(validPoints()).toEqual([])
  })
})

describe('paddedCornerPairs', () => {
  it('returns south-west and north-east corners', () => {
    expect(
      paddedCornerPairs([
        [12, 77],
        [13, 78],
        [12.5, 77.2],
      ]),
    ).toEqual([
      [12, 77],
      [13, 78],
    ])
  })

  it('grows each side by the pad factor like LatLngBounds.pad', () => {
    const [[south, west], [north, east]] = paddedCornerPairs(
      [
        [10, 20],
        [12, 24],
      ],
      0.5,
    )

    expect([south, west, north, east]).toEqual([9, 18, 13, 26])
  })

  it('ignores invalid points when measuring', () => {
    expect(
      paddedCornerPairs([
        [10, 20],
        [null, 99],
        [11, 21],
      ]),
    ).toEqual([
      [10, 20],
      [11, 21],
    ])
  })
})
