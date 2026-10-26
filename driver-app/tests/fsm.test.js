import { describe, expect, it } from 'vitest'
import { fsmConfig, mapStateToOrderStatus, STATE_LABELS } from '../src/stores/job/fsm.js'

describe('job state machine', () => {
  it('starts every job type at IDLE and ends it at COMPLETED', () => {
    for (const [jobType, states] of Object.entries(fsmConfig)) {
      expect(states.IDLE, jobType).toEqual(['ASSIGNED'])
      expect(states.COMPLETED, jobType).toEqual([])
    }
  })

  it('only moves to states the same job type defines', () => {
    for (const [jobType, states] of Object.entries(fsmConfig)) {
      for (const [from, targets] of Object.entries(states)) {
        for (const to of targets) {
          expect(states, `${jobType}: ${from} -> ${to}`).toHaveProperty(to)
        }
      }
    }
  })

  it('reaches COMPLETED from ASSIGNED in every job type', () => {
    for (const [jobType, states] of Object.entries(fsmConfig)) {
      const seen = new Set(['ASSIGNED'])
      const queue = ['ASSIGNED']
      while (queue.length) {
        for (const next of states[queue.shift()]) {
          if (!seen.has(next)) {
            seen.add(next)
            queue.push(next)
          }
        }
      }
      expect(seen.has('COMPLETED'), jobType).toBe(true)
    }
  })

  it('has a driver-facing label for every state except the three that show their raw name', () => {
    const states = new Set(Object.values(fsmConfig).flatMap((s) => Object.keys(s)))
    for (const state of states) {
      if (state === 'CREW_CHECKIN' || state === 'SERVICE_CHECKLIST' || state === 'PACKING_RETURN') continue
      expect(STATE_LABELS, state).toHaveProperty(state)
    }
  })

  it('reports delivery progress to the backend and stays quiet for other states', () => {
    expect(mapStateToOrderStatus('LOAD_VERIFICATION')).toBe('CONFIRMED')
    expect(mapStateToOrderStatus('POD_CAPTURE')).toBe('IN_TRANSIT')
    expect(mapStateToOrderStatus('COMPLETED')).toBe('DELIVERED')
    expect(mapStateToOrderStatus('PACKING')).toBeNull()
  })
})
