import { ref } from 'vue'
import { normalizeErrorMessage, logAndNormalizeError } from '@/utils/errorMessage'

/**
 * 统一异步任务状态管理
 * @param {{ onError?: (err: unknown, message: string) => void }} options
 */
export function useAsyncTask(options = {}) {
  const loading = ref(false)
  const error = ref('')
  const result = ref(null)
  let lastTaskFn = null

  async function run(taskFn) {
    lastTaskFn = taskFn
    loading.value = true
    error.value = ''
    try {
      const data = await taskFn()
      result.value = data
      return data
    } catch (err) {
      const message = logAndNormalizeError(err, 'useAsyncTask')
      error.value = message
      if (options.onError) options.onError(err, message)
      throw err
    } finally {
      loading.value = false
    }
  }

  function reset() {
    loading.value = false
    error.value = ''
    result.value = null
    lastTaskFn = null
  }

  async function retry() {
    if (!lastTaskFn) return undefined
    return run(lastTaskFn)
  }

  return { loading, error, result, run, reset, retry }
}
