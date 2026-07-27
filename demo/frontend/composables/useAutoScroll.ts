import { ref } from 'vue'

/**
 * Intelligent auto-scroll: sticks to the bottom while the user is near it, but stops
 * yanking them down if they scroll up to re-read. Threshold = 50px from the bottom.
 */
export function useAutoScroll() {
  const el = ref<HTMLElement | null>(null)
  const stuck = ref(true)

  function onScroll() {
    const node = el.value
    if (!node) return
    stuck.value = node.scrollHeight - node.scrollTop - node.clientHeight < 50
  }

  function scrollToBottom(force = false) {
    const node = el.value
    if (!node || (!stuck.value && !force)) return
    node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' })
  }

  return { el, stuck, onScroll, scrollToBottom }
}
