import { onMounted, onActivated } from 'vue'
import { getMistakeBookVersion } from '@/utils/mistakeRefresh'

/**
 * 页面进入 / 返回时刷新数据
 * @param {() => void | Promise<void>} callback
 * @param {{ smart?: boolean, minInterval?: number, staleInterval?: number }} options
 *   smart: 结合错题本版本号与时间去重，避免频繁请求
 */
export function usePageRefresh(callback, options = {}) {
  const { smart = false, minInterval = 400, staleInterval = 30000 } = options

  let inFlight = false
  let lastLoadedVersion = -1
  let lastLoadedAt = 0

  async function invoke({ force = false } = {}) {
    if (inFlight) return

    const now = Date.now()
    if (!force && lastLoadedAt && now - lastLoadedAt < minInterval) return

    if (smart && !force && lastLoadedAt) {
      const currentVersion = getMistakeBookVersion()
      const stale = currentVersion !== lastLoadedVersion
      const aged = now - lastLoadedAt > staleInterval
      if (!stale && !aged) return
    }

    inFlight = true
    try {
      await callback()
      lastLoadedVersion = getMistakeBookVersion()
      lastLoadedAt = Date.now()
    } finally {
      inFlight = false
    }
  }

  onMounted(() => invoke({ force: true }))

  onActivated(() => {
    if (smart) invoke({ force: false })
    else invoke({ force: true })
  })

  return { refresh: () => invoke({ force: true }) }
}
