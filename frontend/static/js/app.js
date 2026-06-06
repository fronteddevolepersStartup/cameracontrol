/**
 * Zavod Monitoring - Frontend JavaScript
 * - WebSocket orqali real-time video stream
 * - Transport va ishchi loglarini yangilash
 * - API so'rovlar
 */

// ═══════════════════════════════════════════════
// SOZLAMALAR
// ═══════════════════════════════════════════════
const API = '';          // Bir xil serverda ishlaydi
let videoWS = null;
let hodisaWS = null;
let statistikaTimer = null;

// ═══════════════════════════════════════════════
// VAQT KO'RSATGICH
// ═══════════════════════════════════════════════
function vaqtYangilash() {
  const el = document.getElementById('sana-vaqt');
  if (!el) return;
  const h = new Date();
  const kun = ['Yakshanba','Dushanba','Seshanba','Chorshanba','Payshanba','Juma','Shanba'];
  el.textContent = `${kun[h.getDay()]}  ${h.toLocaleDateString('uz')}  ${h.toLocaleTimeString('uz')}`;
}
setInterval(vaqtYangilash, 1000);
vaqtYangilash();

// ═══════════════════════════════════════════════
// VIDEO WEBSOCKET
// ═══════════════════════════════════════════════
function videoWSUlash() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  videoWS = new WebSocket(`${proto}://${location.host}/ws/video`);

  videoWS.onopen = () => {
    console.log('[Video WS] Ulandi');
    document.getElementById('kamera-overlay').classList.add('yashirin');
    document.getElementById('kamera-holat').textContent = 'JONLI';
    document.getElementById('kamera-holat').className = 'badge yashil';
  };

  videoWS.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.tur === 'video' && data.kadr) {
      document.getElementById('video-kadr').src = 'data:image/jpeg;base64,' + data.kadr;
    }
  };

  videoWS.onclose = () => {
    console.log('[Video WS] Uzildi, qayta ulanmoqda...');
    document.getElementById('kamera-holat').textContent = 'UZILDI';
    document.getElementById('kamera-holat').className = 'badge qizil';
    document.getElementById('kamera-overlay').classList.remove('yashirin');
    document.getElementById('kamera-overlay').innerHTML = '<span>📷 Kameraga ulanmoqda...</span>';
    setTimeout(videoWSUlash, 3000);
  };

  videoWS.onerror = (e) => {
    console.error('[Video WS] Xatolik:', e);
  };
}

// ═══════════════════════════════════════════════
// HODISALAR WEBSOCKET
// ═══════════════════════════════════════════════
function hodisaWSUlash() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  hodisaWS = new WebSocket(`${proto}://${location.host}/ws/hodisalar`);

  hodisaWS.onopen = () => {
    console.log('[Hodisa WS] Ulandi');
    document.getElementById('ws-holat').textContent = 'Ulangan';
    document.getElementById('ws-holat').className = 'badge yashil';
  };

  hodisaWS.onmessage = (e) => {
    const data = JSON.parse(e.data);

    if (data.tur === 'transport') {
      // WebSocket faqat ko'rsatadi, bazaga YOZMAYDI - 2 marta muammo yo'q
      transportJadvalQoshish(data["malumot"], true);
      hodisaQoshish('transport', data["malumot"]);
      statistikaYangilash();
    } else if (data.tur === 'ishchi') {
      ishchiJadvalQoshish(data["malumot"], true);
      hodisaQoshish('ishchi', data["malumot"]);
      statistikaYangilash();
    }
  };

  hodisaWS.onclose = () => {
    document.getElementById('ws-holat').textContent = 'Uzildi';
    document.getElementById('ws-holat').className = 'badge qizil';
    setTimeout(hodisaWSUlash, 3000);
  };
}

// ═══════════════════════════════════════════════
// JADVAL FUNKSIYALARI
// ═══════════════════════════════════════════════
function vaqtFormat(v) {
  if (!v) return '—';
  return v.replace('T', ' ').substring(0, 16);
}

function harakatBadge(harakat) {
  if (harakat === 'kirdi') return `<span class="harakat-kirdi">▶ Kirdi</span>`;
  if (harakat === 'chiqdi') return `<span class="harakat-chiqdi">◀ Chiqdi</span>`;
  return harakat;
}

function transportJadvalQoshish(d, yangi = false) {
  const tbody = document.getElementById('transport-tbody');
  if (!tbody) return;

  // Bo'sh satrni olib tashlash
  const bosh = tbody.querySelector('.boʻsh');
  if (bosh) bosh.parentElement.remove();

  const tr = document.createElement('tr');
  if (yangi) tr.classList.add('yangi');
  tr.innerHTML = `
    <td>${vaqtFormat(d.vaqt)}</td>
    <td><strong>${d.raqam || '—'}</strong></td>
    <td>${d.tur || '—'}</td>
    <td>${d.rang || '—'}</td>
    <td>${d.davlat || '—'}</td>
    <td>${d.viloyat || '—'}</td>
    <td>${harakatBadge(d.harakat)}</td>
  `;
  tbody.insertBefore(tr, tbody.firstChild);

  // Maksimal 100 satr
  while (tbody.children.length > 100) tbody.removeChild(tbody.lastChild);
}

function ishchiJadvalQoshish(d, yangi = false) {
  const tbody = document.getElementById('ishchi-tbody');
  if (!tbody) return;

  const bosh = tbody.querySelector('.boʻsh');
  if (bosh) bosh.parentElement.remove();

  const tr = document.createElement('tr');
  if (yangi) tr.classList.add('yangi');
  tr.innerHTML = `
    <td>${vaqtFormat(d.vaqt)}</td>
    <td><strong>${d.ism || 'Noma\'lum'}</strong></td>
    <td>${harakatBadge(d.harakat)}</td>
  `;
  tbody.insertBefore(tr, tbody.firstChild);
  while (tbody.children.length > 100) tbody.removeChild(tbody.lastChild);
}

// ═══════════════════════════════════════════════
// HODISALAR LENTA
// ═══════════════════════════════════════════════
function hodisaQoshish(tur, d) {
  const lenta = document.getElementById('hodisalar-lenta');
  if (!lenta) return;

  const div = document.createElement('div');
  div.className = `hodisa ${tur}`;

  const vaqt = new Date().toLocaleTimeString('uz');

  if (tur === 'transport') {
    div.innerHTML = `
      <strong>${vaqt}</strong> — 
      ${d.tur || 'Transport'} 
      <strong>${d.raqam || ''}</strong> 
      ${d.harakat === 'kirdi' ? '▶ KIRDI' : '◀ CHIQDI'} | 
      ${d.rang || ''} | ${d.davlat || ''} / ${d.viloyat || ''}
    `;
  } else if (tur === 'ishchi') {
    div.innerHTML = `
      <strong>${vaqt}</strong> — 
      👤 <strong>${d.ism || "Noma'lum"}</strong> aniqlandi
    `;
  }

  lenta.insertBefore(div, lenta.firstChild);
  while (lenta.children.length > 50) lenta.removeChild(lenta.lastChild);
}

// ═══════════════════════════════════════════════
// STATISTIKA YANGILASH
// ═══════════════════════════════════════════════
async function statistikaYangilash() {
  try {
    const r = await fetch('/api/statistika');
    const d = await r.json();

    document.getElementById('bugun-kirdi').textContent =
      d.bugun_transport?.['kirdi'] ?? 0;
    document.getElementById('bugun-chiqdi').textContent =
      d.bugun_transport?.['chiqdi'] ?? 0;
    document.getElementById('bugun-ishchi').textContent =
      d.bugun_ishchilar ?? 0;
    document.getElementById('jami-transport').textContent =
      d.jami_transport ?? 0;
  } catch(e) {
    console.warn('[Statistika] Xatolik:', e);
  }
}

// ═══════════════════════════════════════════════
// MA'LUMOTLARNI YUKLASH
// ═══════════════════════════════════════════════
async function malumotlarYuklash() {
  try {
    const [tr, ir] = await Promise.all([
      fetch('/api/transport?limit=50').then(r => r.json()),
      fetch('/api/ishchilar?limit=50').then(r => r.json()),
    ]);

    tr.forEach(d => transportJadvalQoshish(d));
    ir.forEach(d => ishchiJadvalQoshish(d));
  } catch(e) {
    console.warn('[Malumot] Yuklashda xatolik:', e);
  }
}

// ═══════════════════════════════════════════════
// TUGMA FUNKSIYALARI
// ═══════════════════════════════════════════════
async function transportSkan(harakat) {
  xabarKorsatish(`⏳ ${harakat === 'kirdi' ? 'Kirdi' : 'Chiqdi'} skaplanmoqda...`, 'info');

  try {
    const r = await fetch(`/api/transport/${harakat}`, { method: 'POST' });
    const d = await r.json();

    if (d.holat === 'ok') {
      const m = d["malumot"];
      xabarKorsatish(
        `✅ ${m.tur} ${harakat.toUpperCase()}: ${m.raqam} | ${m.rang} | ${m.davlat}/${m.viloyat}`,
        'muvaffaq'
      );
      transportDetalKorsatish(m);
      transportJadvalQoshish({ ...m, vaqt: new Date().toISOString() }, true);
      statistikaYangilash();
    } else {
      xabarKorsatish('❌ ' + (d.xabar || 'Xatolik yuz berdi'), 'xato');
    }
  } catch(e) {
    xabarKorsatish('❌ Server bilan bog\'lanishda xatolik', 'xato');
  }
}

async function ishchiSkan() {
  xabarKorsatish('⏳ Ishchilar skaplanmoqda...', 'info');
  try {
    const r = await fetch('/api/ishchi/skan', { method: 'POST' });
    const d = await r.json();
    if (d.son > 0) {
      xabarKorsatish(`✅ ${d.son} ta ishchi aniqlandi`, 'muvaffaq');
      d.ishchilar.forEach(i => {
        ishchiJadvalQoshish({ ism: i.ism, harakat: 'aniqlandi', vaqt: new Date().toISOString() }, true);
      });
      tabAlmash('ishchi');
      statistikaYangilash();
    } else {
      xabarKorsatish('ℹ️ Ishchi topilmadi', 'info');
    }
  } catch(e) {
    xabarKorsatish('❌ Xatolik: ' + e.message, 'xato');
  }
}

function excelYuklash() {
  const davrlar = [
    { qiy: 'bugun',   nom: '📅 Bugun' },
    { qiy: 'hafta',   nom: '📆 Bu hafta' },
    { qiy: 'oy',      nom: '🗓️ Bu oy' },
    { qiy: 'hammasi', nom: '📂 Hammasi' },
  ];

  // Oddiy tanlash dialogi
  const tanlangan = prompt(
    'Qaysi davr uchun hisobot?\n\n' +
    '1 - Bugun\n2 - Bu hafta\n3 - Bu oy\n4 - Hammasi\n\nRaqam kiriting (1-4):',
    '1'
  );
  const idx = parseInt(tanlangan) - 1;
  if (isNaN(idx) || idx < 0 || idx > 3) {
    xabarKorsatish('❌ Noto\'g\'ri tanlov', 'xato');
    return;
  }
  const davr = davrlar[idx].qiy;
  xabarKorsatish(`⏳ ${davrlar[idx].nom} uchun Excel tayyorlanmoqda...`, 'muvaffaq');
  window.open(`/api/excel/yuklash?davr=${davr}`, '_blank');
}

// ═══════════════════════════════════════════════
// YORDAMCHI FUNKSIYALAR
// ═══════════════════════════════════════════════
function xabarKorsatish(matn, tur = 'muvaffaq') {
  const el = document.getElementById('natija-xabar');
  el.textContent = matn;
  el.className = `natija-xabar ${tur}`;
  el.style.display = 'block';
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.style.display = 'none'; }, 5000);
}

function transportDetalKorsatish(d) {
  const karta = document.getElementById('oxirgi-transport-karta');
  const detal = document.getElementById('transport-detal');
  karta.style.display = 'block';

  const maydonlar = [
    ['🔢 Raqam',   d.raqam],
    ['🚛 Tur',     d.tur],
    ['🎨 Rang',    d.rang],
    ['🌍 Davlat',  d.davlat],
    ['📍 Viloyat', d.viloyat],
    ['↔️ Harakat', d.harakat === 'kirdi' ? '▶ KIRDI' : '◀ CHIQDI'],
    ['🎯 Ishonch', `${(d.ishonch * 100).toFixed(0)}%`],
    ['📸 Rasm',    d.rasm_yol ? '✅ Saqlandi' : '❌ Yo\'q'],
  ];

  detal.innerHTML = maydonlar.map(([nom, qiy]) => `
    <div class="detal-qator">
      <div class="detal-nom">${nom}</div>
      <div class="detal-qiy">${qiy || '—'}</div>
    </div>
  `).join('');
}

function tabAlmash(nom) {
  document.getElementById('panel-transport').style.display = nom === 'transport' ? 'block' : 'none';
  document.getElementById('panel-ishchi').style.display   = nom === 'ishchi'    ? 'block' : 'none';
  document.getElementById('tab-transport').className = 'tab' + (nom === 'transport' ? ' faol' : '');
  document.getElementById('tab-ishchi').className    = 'tab' + (nom === 'ishchi'    ? ' faol' : '');
}

// ═══════════════════════════════════════════════
// ISHGA TUSHIRISH
// ═══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  malumotlarYuklash();
  statistikaYangilash();
  videoWSUlash();
  hodisaWSUlash();

  // Har 30 sekundda statistika yangilanadi
  statistikaTimer = setInterval(statistikaYangilash, 30000);

  hodisaQoshish('info', { ism: 'Tizim', harakat: 'ishga tushdi' });
  console.log('[App] Zavod Monitoring ishga tushdi ✓');
});
