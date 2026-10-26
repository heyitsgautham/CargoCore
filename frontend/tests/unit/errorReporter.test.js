import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import {
  installErrorReporting,
  reportClientError,
  resetErrorReporterForTests,
} from '@/utils/errorReporter'

let router

beforeEach(() => {
  resetErrorReporterForTests()
  router = stubFetch([['POST', '/api/v1/client-errors', { status: 'accepted' }]])
})

describe('client error reporter', () => {
  it('posts the message, stack, scope and context', () => {
    const error = new Error('boom')
    expect(reportClientError(error, { scope: 'picking board', context: { orderId: 'QC-1' } })).toBe(
      true,
    )

    const call = router.calls[0]
    expect(call.url).toContain('/api/v1/client-errors')
    expect(call.body).toMatchObject({
      level: 'error',
      message: 'boom',
      scope: 'picking-board',
      context: { orderId: 'QC-1' },
    })
    expect(call.body.stack).toContain('boom')
  })

  it('drops back-to-back repeats and stops after 20 reports', () => {
    reportClientError('same')
    expect(reportClientError('same')).toBe(false)
    for (let i = 0; i < 25; i += 1) reportClientError(`error ${i}`)
    expect(router.calls).toHaveLength(20)
  })

  it('reports Vue errors and still hands them to an earlier handler', () => {
    const earlier = vi.fn()
    const app = { config: { errorHandler: earlier } }
    installErrorReporting(app)

    app.config.errorHandler(
      new Error('render failed'),
      { $options: { __name: 'PickWaveCard' } },
      'render',
    )

    expect(router.calls[0].body).toMatchObject({
      scope: 'PickWaveCard',
      context: { info: 'render' },
    })
    expect(earlier).toHaveBeenCalled()
  })
})
