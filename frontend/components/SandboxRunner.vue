<template>
  <div>
    <div class="flex items-center gap-2 text-xs text-slate-500">
      <span class="h-2 w-2 rounded-full" :class="dotClass" />
      <span>{{ statusText }}</span>
      <button
        v-if="code"
        class="ml-auto rounded border border-slate-300 px-2 py-0.5 hover:border-slate-500"
        :disabled="status === 'running'"
        @click="run"
      >
        Re-run
      </button>
    </div>

    <!-- The sandbox. allow-scripts WITHOUT allow-same-origin => opaque origin (no host DOM /
         cookies / storage). No allow-top-navigation / allow-forms / allow-popups. The generated
         code renders whatever UI it wants INTO this frame's own DOM — isolation makes that safe. -->
    <iframe
      v-if="runId"
      :key="runId"
      ref="frame"
      sandbox="allow-scripts"
      :srcdoc="SRCDOC"
      title="sandbox output"
      class="mt-2 block w-full max-w-full rounded-lg border border-slate-200 bg-white"
      :style="{ height: `${height}px` }"
    />

    <p v-if="errorMessage" class="mt-2 rounded bg-rose-50 px-3 py-2 text-sm text-rose-700">
      {{ errorMessage }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { GenFlight } from '~/types/generative'

const props = defineProps<{ code: string, flights: GenFlight[] }>()
const emit = defineEmits<{ done: [], error: [message: string] }>()

// Bootstrap loaded into the sandbox. Generated code arrives via postMessage (never interpolated
// into this HTML), then renders freely into document.body. CSP still blocks all network
// (connect-src 'none') and any external resource; only inline styles / data: images are allowed.
const SRCDOC = `<!doctype html><html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; base-uri 'none'; form-action 'none';">
<style>html,body{margin:0}body{font:13px/1.4 system-ui,sans-serif;color:#0b1020;padding:12px}</style>
</head><body><script>
(function(){
  var pending = {}, seq = 0;
  function call(fn, args){
    return new Promise(function(resolve, reject){
      var id = ++seq; pending[id] = { resolve: resolve, reject: reject };
      parent.postMessage({ type: 'call', id: id, fn: fn, args: args }, '*');
    });
  }
  var loadFlights = function(){ return call('loadFlights', []); };
  function sendHeight(){
    try {
      var de = document.documentElement, b = document.body;
      var h = Math.max(de ? de.scrollHeight : 0, b ? b.scrollHeight : 0, b ? Math.ceil(b.getBoundingClientRect().height) : 0);
      parent.postMessage({ type: 'height', value: h }, '*');
    } catch (e) {}
  }
  function measureSoon(){
    // Layout may not be final right after innerHTML; measure across frames + a couple of ticks.
    sendHeight();
    requestAnimationFrame(function(){ requestAnimationFrame(sendHeight); });
    setTimeout(sendHeight, 80);
    setTimeout(sendHeight, 250);
    try { new ResizeObserver(sendHeight).observe(document.documentElement); } catch (e) {}
  }
  window.addEventListener('message', function(e){
    if (e.source !== window.parent) return;
    var msg = e.data || {};
    if (msg.type === 'result') { var p = pending[msg.id]; if (p) { delete pending[msg.id]; p.resolve(msg.value); } }
    else if (msg.type === 'error_result') { var q = pending[msg.id]; if (q) { delete pending[msg.id]; q.reject(new Error(msg.message)); } }
    else if (msg.type === 'run') {
      (async function(){
        try {
          var runner = new Function('loadFlights', '"use strict"; return (async function(){\\n' + msg.code + '\\n})();');
          await runner(loadFlights);
          measureSoon();
          parent.postMessage({ type: 'done' }, '*');
        } catch (err) {
          parent.postMessage({ type: 'error', message: String(err && err.message ? err.message : err) }, '*');
        }
      })();
    }
  });
  parent.postMessage({ type: 'ready' }, '*');
})();
` + '<' + '/script></body></html>'

const frame = ref<HTMLIFrameElement | null>(null)
const runId = ref(0)
const height = ref(160)
const status = ref<'idle' | 'running' | 'done' | 'error'>('idle')
const errorMessage = ref('')
let timer: ReturnType<typeof setTimeout> | null = null

const dotClass = computed(() => ({
  idle: 'bg-slate-300',
  running: 'bg-amber-400 animate-pulse',
  done: 'bg-emerald-500',
  error: 'bg-rose-500',
}[status.value]))
const statusText = computed(() => ({
  idle: 'sandbox idle',
  running: 'running in sandbox…',
  done: 'rendered in sandbox',
  error: 'sandbox error',
}[status.value]))

function post(message: object) {
  frame.value?.contentWindow?.postMessage(message, '*')
}

function clearTimer() {
  if (timer) { clearTimeout(timer); timer = null }
}

function fail(message: string) {
  clearTimer()
  status.value = 'error'
  errorMessage.value = message
  emit('error', message)
}

function onMessage(e: MessageEvent) {
  if (!frame.value || e.source !== frame.value.contentWindow) return
  const msg = e.data || {}
  switch (msg.type) {
    case 'ready':
      post({ type: 'run', code: props.code })
      break
    case 'call':
      handleCall(msg)
      break
    case 'height':
      if (Number.isFinite(msg.value)) height.value = Math.min(2000, Math.max(120, Math.ceil(msg.value)))
      break
    case 'done':
      clearTimer()
      status.value = 'done'
      emit('done')
      break
    case 'error':
      fail(msg.message || 'Unknown sandbox error')
      break
  }
}

// The whitelist. The sandbox can invoke ONLY this; anything else is rejected.
function handleCall(msg: { id: number, fn: string, args: unknown[] }) {
  try {
    if (msg.fn === 'loadFlights') {
      // Deep-copy to plain objects: postMessage can't structured-clone Vue reactive proxies.
      post({ type: 'result', id: msg.id, value: JSON.parse(JSON.stringify(props.flights)) })
      return
    }
    throw new Error(`function not allowed: ${msg.fn}`)
  }
  catch (err) {
    post({ type: 'error_result', id: msg.id, message: (err as Error).message })
  }
}

function run() {
  if (!props.code) return
  clearTimer()
  errorMessage.value = ''
  status.value = 'running'
  height.value = 160
  runId.value++ // remount the iframe → fresh, stateless sandbox each run
  timer = setTimeout(() => fail('Sandbox timed out (5s).'), 5000)
}

onMounted(() => {
  window.addEventListener('message', onMessage)
  // The component usually mounts with `code` already set (result arrives first).
  if (props.code) run()
})
onBeforeUnmount(() => {
  window.removeEventListener('message', onMessage)
  clearTimer()
})

// Handles subsequent regenerations while the runner stays mounted.
watch(() => props.code, run)
defineExpose({ run })
</script>
