/**
 * Registers the design-system web components used by approach #5 (server-streamed UI).
 * These are standard custom elements — framework-agnostic ("write once, render everywhere").
 * The server streams `<flight-card …>` tags; the browser upgrades them here. Values are set with
 * textContent (never innerHTML) so attribute content can't inject markup.
 */
class FlightCard extends HTMLElement {
  connectedCallback() {
    if (this.dataset.rendered) return
    this.dataset.rendered = '1'
    this.style.display = 'block'

    const g = (a: string) => this.getAttribute(a) ?? ''
    const delay = Number(g('delay'))
    const tone = delay ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'

    const el = (tag: string, cls: string, text?: string) => {
      const node = document.createElement(tag)
      node.className = cls
      if (text !== undefined) node.textContent = text
      return node
    }

    const wrap = el('div', 'flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3')
    const left = el('div', 'min-w-0 flex-1')
    const row = el('div', 'flex items-center gap-2')
    row.append(el('code', 'text-sm font-semibold', g('fid')), el('span', 'text-xs text-slate-400', g('date')))
    left.append(row, el('div', 'text-xs text-slate-500', g('route')))
    const badge = el('span', `rounded-full px-2 py-0.5 text-xs font-medium ${tone}`, delay ? `${delay}m late` : 'on time')
    const price = el('div', 'font-semibold text-slate-900', `€${g('price')}`)
    wrap.append(left, badge, price)
    this.replaceChildren(wrap)
  }
}

export default defineNuxtPlugin(() => {
  if (!customElements.get('flight-card')) customElements.define('flight-card', FlightCard)
})
