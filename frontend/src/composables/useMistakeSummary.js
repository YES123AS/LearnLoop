import { ref } from 'vue'
import { getMistakeBook } from '@/api/index'
import { getStudentId } from '@/utils/studentId'
import { buildMistakeStats } from '@/utils/mistakeStats'

/**
 * 统一错题本加载与统计
 * @param {{ defaultStatus?: string, silent?: boolean, onLoaded?: (stats: object, mistakes: array) => void | Promise<void> }} options
 */
export function useMistakeSummary(options = {}) {
  const { defaultStatus, silent = true, onLoaded } = options

  const mistakes = ref([])
  const stats = ref(buildMistakeStats([]))
  const loading = ref(false)
  const error = ref('')

  async function loadMistakes(status = defaultStatus) {
    loading.value = true
    error.value = ''
    try {
      const data = await getMistakeBook(getStudentId(), status, { silent })
      mistakes.value = data.mistakes || []
      stats.value = buildMistakeStats(mistakes.value)
      if (onLoaded) await onLoaded(stats.value, mistakes.value)
      return { mistakes: mistakes.value, stats: stats.value }
    } catch (err) {
      mistakes.value = []
      stats.value = buildMistakeStats([])
      if (!silent) {
        error.value = err?.message || '错题数据加载失败'
        console.error('[useMistakeSummary]', err)
      }
      return { mistakes: [], stats: stats.value }
    } finally {
      loading.value = false
    }
  }

  function refresh() {
    return loadMistakes(defaultStatus)
  }

  return { mistakes, stats, loading, error, loadMistakes, refresh }
}
