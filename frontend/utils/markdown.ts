import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// Markdown renderer with syntax highlighting. `html: false` keeps model output safe
// (raw HTML is escaped), which matters because we render the result with v-html.
const md: MarkdownIt = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(code, { language: lang }).value}</code></pre>`
      }
      catch {
        // fall through to default escaping
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(code)}</code></pre>`
  },
})

export function renderMarkdown(source: string): string {
  return md.render(source)
}
