import { afterEach, describe, expect, it, vi } from 'vitest'
import { createChatSSE } from './api'

const encoder = new TextEncoder()

function mockSseResponse(chunks: string[]) {
  const stream = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  })
  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': 'text/event-stream' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('createChatSSE', () => {
  it('parses text and chart events', async () => {
    const fetchMock = vi.fn(async () =>
      mockSseResponse([
        'event: text\ndata: Hello\n\n',
        'event: chart\ndata: {"type":"bar","title":"Sales","data":[{"name":"A","value":1}]}\n\n',
        'event: done\ndata: {}\n\n',
      ]),
    )
    vi.stubGlobal('fetch', fetchMock)

    const onText = vi.fn()
    const onChart = vi.fn()
    const onDone = vi.fn()

    await createChatSSE({ session_id: 's1', message: 'hi' }).start({ onText, onChart, onDone })

    expect(onText).toHaveBeenCalledWith('Hello')
    expect(onChart).toHaveBeenCalledWith({
      type: 'bar',
      title: 'Sales',
      data: [{ name: 'A', value: 1 }],
    })
    expect(onDone).toHaveBeenCalled()
  })

  it('parses data events with columns and rows', async () => {
    const fetchMock = vi.fn(async () =>
      mockSseResponse([
        'event: data\ndata: {"columns":["Month","Sales"],"rows":[{"name":"Jan","value":1200}],"raw":[["Jan",1200]]}\n\n',
      ]),
    )
    vi.stubGlobal('fetch', fetchMock)

    const onData = vi.fn()
    await createChatSSE({ session_id: 's1', message: 'hi' }).start({ onData })

    expect(onData).toHaveBeenCalledWith({
      columns: ['Month', 'Sales'],
      rows: [{ name: 'Jan', value: 1200 }],
      raw: [['Jan', 1200]],
    })
  })

  it('calls onError for error events', async () => {
    const fetchMock = vi.fn(async () => mockSseResponse(['event: error\ndata: boom\n\n']))
    vi.stubGlobal('fetch', fetchMock)

    const onError = vi.fn()
    await createChatSSE({ session_id: 's1', message: 'hi' }).start({ onError })

    expect(onError).toHaveBeenCalledWith('boom')
  })
})
