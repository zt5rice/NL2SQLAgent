import { afterEach, describe, expect, it, vi } from 'vitest'
import { createChatSSE, databaseApi, sessionApi } from './api'

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
        'event: data\ndata: {"columns":["Month","Sales"],"rows":[["Jan",1200],["Feb",900]],"raw":"[[\'Jan\', 1200], [\'Feb\', 900]]"}\n\n',
      ]),
    )
    vi.stubGlobal('fetch', fetchMock)

    const onData = vi.fn()
    await createChatSSE({ session_id: 's1', message: 'hi' }).start({ onData })

    expect(onData).toHaveBeenCalledWith({
      columns: ['Month', 'Sales'],
      rows: [
        ['Jan', 1200],
        ['Feb', 900],
      ],
      raw: "[['Jan', 1200], ['Feb', 900]]",
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

describe('sessionApi', () => {
  it('list unwraps the { sessions } envelope from the backend', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            sessions: [
              { id: 's1', title: 'A', created_at: '2026-08-14T00:00:00', updated_at: '2026-08-14T00:00:00' },
            ],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )
    const sessions = await sessionApi.list()
    expect(sessions).toHaveLength(1)
    expect(sessions[0].id).toBe('s1')
  })

  it('delete handles an empty 204 response', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 204 })))
    await expect(sessionApi.delete('s1')).resolves.toBeUndefined()
  })

  it('throws the backend detail on non-2xx responses', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Session not found' }), { status: 404 }),
      ),
    )
    await expect(sessionApi.delete('missing')).rejects.toThrow('Session not found')
  })
})

describe('databaseApi', () => {
  it('tables returns the table list', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ tables: ['sales', 'employees'] }), { status: 200 }),
      ),
    )
    await expect(databaseApi.tables()).resolves.toEqual({
      tables: ['sales', 'employees'],
    })
  })

  it('schema returns typed database schema', async () => {
    const schema = {
      tables: [
        {
          name: 'sales',
          columns: [{ name: 'id', type: 'INTEGER', nullable: true, default: null, primary_key: true }],
          sample_rows: [{ id: 1 }],
          row_count: 15,
        },
      ],
    }
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(schema), { status: 200 })))
    await expect(databaseApi.schema()).resolves.toEqual(schema)
  })
})
