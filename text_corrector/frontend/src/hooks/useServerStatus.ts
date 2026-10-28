/**
 * Hook that polls GET /health until the Kazakh model is loaded.
 *
 * The hosted server (Hugging Face Space) sleeps when nobody uses it and needs
 * about a minute to wake up and load the model, so the first checks may fail.
 */
import { useEffect, useState } from 'react'
import { checkHealth } from '@/services/api'

export type ServerStatus = 'connecting' | 'waking' | 'ready' | 'unavailable'

const RETRY_MS = 3_000
// Waking normally takes about a minute; after this long, say it is down
const GIVE_UP_MS = 180_000

export function useServerStatus(): ServerStatus {
  const [status, setStatus] = useState<ServerStatus>('connecting')

  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined
    const started = Date.now()

    const poll = async () => {
      try {
        const health = await checkHealth()
        if (cancelled) return
        if (health.details?.kazakh_model_ready === 'True') {
          setStatus('ready')
          return
        }
      } catch {
        // asleep, starting or unreachable — keep trying
      }
      if (cancelled) return
      setStatus(Date.now() - started > GIVE_UP_MS ? 'unavailable' : 'waking')
      timer = setTimeout(poll, RETRY_MS)
    }

    poll()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [])

  return status
}
