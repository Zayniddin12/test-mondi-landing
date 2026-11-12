<script setup lang="ts">
import '~/assets/main.css'

type Item = { id: string; category: string; name: string; desc: string; price: number; emoji: string }
type Cat = { id: string; title: string }

const { data: payMethods } = await useFetch<{ methods: { code: string; name: string; type: string }[] }>('/api/payment-methods')
const { data: menu, error: menuError } = await useFetch<{ categories: Cat[]; items: Item[] }>('/api/menu')

const activeCat = ref('all')
const shown = computed(() =>
  (menu.value?.items ?? []).filter((i) => activeCat.value === 'all' || i.category === activeCat.value),
)

// --- savat ---
const cart = reactive<Record<string, number>>({})
const lines = computed(() =>
  (menu.value?.items ?? []).filter((i) => cart[i.id]).map((i) => ({ ...i, qty: cart[i.id] })),
)
const subtotal = computed(() => lines.value.reduce((s, l) => s + l.price * l.qty, 0))
const count = computed(() => lines.value.reduce((s, l) => s + l.qty, 0))
const add = (id: string) => (cart[id] = (cart[id] || 0) + 1)
const sub = (id: string) => {
  if (cart[id] > 1) cart[id]--
  else delete cart[id]
}
const money = (n: number) => n.toLocaleString('ru-RU') + " so'm"

// --- buyurtma formasi ---
const showCart = ref(false)
const form = reactive({ name: '', phone: '+998', address: '', district: '', note: '', payment: 'naqd' })
const coords = ref<{ lat: number; lng: number } | null>(null)
const geoMsg = ref('')
const quote = ref<{ delivery_fee: number; distance_km: number; eta_min: number } | null>(null)
const sending = ref(false)
const errorMsg = ref('')

async function locate() {
  geoMsg.value = 'Aniqlanmoqda…'
  if (!navigator.geolocation) return (geoMsg.value = 'Brauzer joylashuvni qo‘llamaydi')
  navigator.geolocation.getCurrentPosition(
    async (p) => {
      coords.value = { lat: p.coords.latitude, lng: p.coords.longitude }
      geoMsg.value = 'Joylashuv aniqlandi ✓'
      try {
        quote.value = await $fetch('/api/quote', { query: coords.value })
      } catch {
        quote.value = null
      }
    },
    () => (geoMsg.value = 'Ruxsat berilmadi — manzilni qo‘lda yozing'),
    { timeout: 8000 },
  )
}

// --- buyurtma yuborish ---
const order = ref<any>(null)
const status = ref<any>(null)
let timer: any

async function submit() {
  errorMsg.value = ''
  sending.value = true
  try {
    const res: any = await $fetch('/api/orders', {
      method: 'POST',
      body: {
        customer: { name: form.name.trim(), phone: form.phone.replace(/\s/g, '') },
        address: {
          text: form.address.trim(),
          district: form.district.trim() || undefined,
          ...(coords.value ?? {}),
        },
        items: lines.value.map((l) => ({ id: l.id, qty: l.qty })),
        payment_method: form.payment,
        return_url: location.origin + '/?order={ID}',
        return_error_url: location.origin + '/?order={ID}&failed=1',
        note: form.note.trim() || undefined,
      },
    })
    order.value = res
    status.value = res
    showCart.value = false
    Object.keys(cart).forEach((k) => delete cart[k])
    if (res.payment?.pay_url) {
      try { sessionStorage.setItem('mondi_order', res.external_id) } catch {}
      location.href = res.payment.pay_url // Multicard / ilova to'lov sahifasiga
      return
    }
    startPolling()
  } catch (e: any) {
    const d = e?.data?.detail
    errorMsg.value = Array.isArray(d)
      ? d.map((x: any) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ')
      : d || 'Buyurtma yuborilmadi'
  } finally {
    sending.value = false
  }
}

function startPolling() {
  clearInterval(timer)
  const tick = async () => {
    try {
      const [st, pay]: any[] = await Promise.all([
        $fetch(`/api/orders/${order.value.external_id}`),
        status.value?.pay_status === 'paid' || form.payment === 'naqd' ? null : $fetch(`/api/orders/${order.value.external_id}/payment`),
      ])
      status.value = { ...st, payment: pay?.payment ?? status.value?.payment }
      if (['delivered', 'cancelled'].includes(status.value.status)) clearInterval(timer)
    } catch {}
  }
  timer = setInterval(tick, 15000)
  tick()
}

// to'lov havolasini qayta olish / usulni almashtirish
const payMethod = ref('')
async function pay() {
  errorMsg.value = ''
  try {
    const r: any = await $fetch(`/api/orders/${order.value.external_id}/pay`, {
      method: 'POST',
      body: {
        method: payMethod.value || payMethods.value?.methods?.[0]?.code,
        return_url: location.origin + `/?order=${order.value.external_id}`,
        return_error_url: location.origin + `/?order=${order.value.external_id}&failed=1`,
      },
    })
    if (r.pay_url) location.href = r.pay_url
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || 'To‘lov havolasini olib bo‘lmadi'
  }
}

// to'lovdan qaytgach (?order=ID) kuzatuvni davom ettirish
onMounted(() => {
  const id = (useRoute().query.order as string) || ''
  if (!id) return
  order.value = { external_id: id }
  startPolling()
  history.replaceState(null, '', location.pathname)
})

async function cancel() {
  try {
    status.value = await $fetch(`/api/orders/${order.value.external_id}/cancel`, { method: 'POST', body: {} })
    startPolling()
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || 'Bekor qilib bo‘lmadi'
  }
}
const newOrder = () => {
  clearInterval(timer)
  order.value = status.value = null
}
onBeforeUnmount(() => clearInterval(timer))

const payLabel = computed(() =>
  ({ paid: "to'langan", pending: "to'lov kutilmoqda" } as Record<string, string>)[status.value?.pay_status] ?? status.value?.pay_status,
)
const steps = ['new', 'assigned', 'onway', 'delivered']
const stepIdx = computed(() => steps.indexOf(status.value?.status))
const total = computed(() => subtotal.value + (quote.value?.delivery_fee ?? 0))
</script>

<template>
  <header class="top">
    <div class="wrap bar">
      <div class="logo">Mondi<span>.</span></div>
      <button class="cart-btn" @click="showCart = true" :disabled="!!order">🛒 Savat <b v-if="count">{{ count }}</b></button>
    </div>
  </header>

  <section class="hero">
    <div class="wrap">
      <h1>Issiq taom va qahva <em>eshigingizgacha</em></h1>
      <p>Menyudan tanlang, buyurtma bering — kuryer Yo'lda orqali yetkazadi.</p>
      <a href="#menu" class="cta">Menyuni ko'rish</a>
    </div>
  </section>

  <main class="wrap" id="menu">
    <!-- Buyurtma kuzatuvi -->
    <section v-if="order" class="track card">
      <h2>Buyurtma {{ order.external_id }}</h2>
      <p class="big">{{ status?.status_text }}</p>
      <ol v-if="status?.status !== 'cancelled'" class="steps">
        <li v-for="(s, i) in ['Qabul qilindi', 'Kuryer restoranga', 'Mijozga yo‘lda', 'Yetkazildi']" :key="s" :class="{ on: i <= stepIdx }">{{ s }}</li>
      </ol>
      <p v-if="status?.courier">Kuryer: <b>{{ status.courier.name }}</b>, {{ status.courier.phone }}<span v-if="status.eta_min"> · ~{{ status.eta_min }} daqiqa</span></p>
      <p v-if="status?.cancel_reason">Sabab: {{ status.cancel_reason }}</p>
      <p class="muted">Taomlar: {{ money(status?.subtotal ?? 0) }} · Yetkazish: {{ money(status?.delivery_fee ?? 0) }} · <b>Jami: {{ money(status?.total ?? 0) }}</b> ({{ payLabel }})</p>
      <div v-if="status?.pay_status === 'pending' && status?.status !== 'cancelled'" class="pay-box">
        <p class="err" v-if="status?.payment?.status === 'expired'">To'lov havolasi muddati tugadi.</p>
        <p class="muted">To'lov kutilmoqda — to'lamaguncha kuryer qidirilmaydi.</p>
        <select v-model="payMethod"><option v-for="m in payMethods?.methods" :key="m.code" :value="m.code">{{ m.name }}</option></select>
        <button class="primary" @click="pay">To'lash</button>
      </div>
      <p v-if="errorMsg" class="err">{{ errorMsg }}</p>
      <div class="row">
        <button v-if="['new', 'assigned'].includes(status?.status)" class="ghost" @click="cancel">Bekor qilish</button>
        <button class="primary" @click="newOrder">Yangi buyurtma</button>
      </div>
    </section>

    <template v-else>
      <p v-if="menuError" class="err">Menyuni yuklab bo'lmadi. Backend ishlayaptimi?</p>
      <nav class="tabs">
        <button :class="{ on: activeCat === 'all' }" @click="activeCat = 'all'">Hammasi</button>
        <button v-for="c in menu?.categories" :key="c.id" :class="{ on: activeCat === c.id }" @click="activeCat = c.id">{{ c.title }}</button>
      </nav>
      <div class="grid">
        <article v-for="i in shown" :key="i.id" class="card item">
          <div class="emoji">{{ i.emoji }}</div>
          <h3>{{ i.name }}</h3>
          <p class="muted">{{ i.desc }}</p>
          <div class="row between">
            <b>{{ money(i.price) }}</b>
            <div v-if="cart[i.id]" class="qty"><button @click="sub(i.id)">−</button>{{ cart[i.id] }}<button @click="add(i.id)">+</button></div>
            <button v-else class="primary sm" @click="add(i.id)">Qo'shish</button>
          </div>
        </article>
      </div>
    </template>
  </main>

  <div v-if="count && !order && !showCart" class="floating">
    <button class="primary" @click="showCart = true">Savatni ochish · {{ count }} ta · {{ money(subtotal) }}</button>
  </div>

  <!-- Savat / checkout -->
  <div v-if="showCart" class="overlay" @click.self="showCart = false">
    <form class="drawer" @submit.prevent="submit">
      <div class="row between"><h2>Savat</h2><button type="button" class="x" @click="showCart = false">✕</button></div>
      <p v-if="!lines.length" class="muted">Savat bo'sh</p>
      <ul class="lines">
        <li v-for="l in lines" :key="l.id">
          <span>{{ l.emoji }} {{ l.name }}</span>
          <div class="qty"><button type="button" @click="sub(l.id)">−</button>{{ l.qty }}<button type="button" @click="add(l.id)">+</button></div>
          <b>{{ money(l.price * l.qty) }}</b>
        </li>
      </ul>

      <template v-if="lines.length">
        <label>Ism<input v-model="form.name" required minlength="2" placeholder="Dilnoza A." /></label>
        <label>Telefon<input v-model="form.phone" required pattern="\+998\d{9}" placeholder="+998901234567" inputmode="tel" /></label>
        <label>Manzil<input v-model="form.address" required minlength="5" placeholder="Ko'cha, uy, xonadon" /></label>
        <label>Tuman<input v-model="form.district" placeholder="Yunusobod" /></label>
        <div class="row"><button type="button" class="ghost sm" @click="locate">📍 Joylashuvimni aniqlash</button><span class="muted">{{ geoMsg }}</span></div>
        <label>Kuryerga izoh<input v-model="form.note" maxlength="500" placeholder="Domofon ishlamaydi…" /></label>
        <label>To'lov usuli
          <select v-model="form.payment">
            <option value="naqd">Naqd (kuryerga)</option>
            <option v-for="m in payMethods?.methods" :key="m.code" :value="m.code">{{ m.name }}</option>
          </select>
        </label>
        <p v-if="form.payment !== 'naqd'" class="muted">Buyurtmadan so'ng to'lov sahifasiga o'tasiz. To'lov tushgach kuryer qidiruvi boshlanadi.</p>

        <div class="sum">
          <div class="row between"><span>Taomlar</span><span>{{ money(subtotal) }}</span></div>
          <div class="row between"><span>Yetkazish</span><span>{{ quote ? money(quote.delivery_fee) : 'Yo\'lda hisoblaydi' }}</span></div>
          <div v-if="quote" class="row between muted"><span>{{ quote.distance_km }} km</span><span>~{{ quote.eta_min }} daqiqa</span></div>
          <div class="row between"><b>Jami</b><b>{{ quote ? money(total) : money(subtotal) + ' +' }}</b></div>
        </div>
        <p v-if="errorMsg" class="err">{{ errorMsg }}</p>
        <button class="primary full" :disabled="sending">{{ sending ? 'Yuborilmoqda…' : 'Buyurtma berish' }}</button>
      </template>
    </form>
  </div>
</template>
