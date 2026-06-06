/**
 * Zavod Monitoring - Frontend JavaScript
 */

const API = '';
let videoWS = null;
let hodisaWS = null;

// ── Vaqt ─────────────────────────────────────
function vaqtYangilash() {
  const el = document.getElementById('sana-vaqt');
  if (!el) return;
  const h = new Date();
  const kun = ['Yakshanba','Dushanba','Seshanba','Chorshanba','Payshanba','Juma','Shanba'];
  el.textContent = kun[h.getDay()] + '  ' + h.toLocaleDateString('uz') + '  ' + h.toLocaleTimeString('uz');
}
setInterval(vaqtYangilash, 1000);
vaqtYangilash();

// ── Video WebSocket ───────────────────────────
function videoWSUlash() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  videoWS = new WebSocket(proto + '://' + location.host + '/ws/video');

  videoWS.onopen = function() {
    console.log('[Video WS] Ulandi');
    document.getElementById('kamera-overlay').classList.add('yashirin');
    document.getElementById('kamera-holat').textContent = 'JONLI';
    document.getElementById('kamera-holat').className = 'badge yashil';
  };

  videoWS.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.tur === 'video' && data.kadr) {
      document.getElementById('kamera-overlay').classList.add('yashirin');
      document.getElementById('video-kadr').src = 'data:image/jpeg;base64,' + data.kadr;
    }
  };

  videoWS.onclose = function() {
    document.getElementById('kamera-holat').textContent = 'UZILDI';
    document.getElementById('kamera-holat').className = 'badge qizil';
    document.getElementById('kamera-overlay').classList.remove('yashirin');
    document.getElementById('kamera-overlay').innerHTML = '<span>Kameraga ulanmoqda...</span>';
    setTimeout(videoWSUlash, 3000);
  };

  videoWS.onerror = function(e) {
    console.error('[Video WS] Xatolik:', e);
  };
}

// ── Hodisalar WebSocket ───────────────────────
function hodisaWSUlash() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  hodisaWS = new WebSocket(proto + '://' + location.host + '/ws/hodisalar');

  hodisaWS.onopen = function() {
    document.getElementById('ws-holat').textContent = 'Ulangan';
    document.getElementById('ws-holat').className = 'badge yashil';
  };

  hodisaWS.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.tur === 'transport') {
      transportJadvalQoshish(data.malumot, true);
      hodisaQoshish('transport', data.malumot);
      statistikaYangilash();
    } else if (data.tur === 'ishchi') {
      ishchiJadvalQoshish(data.malumot, true);
      hodisaQoshish('ishchi', data.malumot);
      statistikaYangilash();
    }
  };

  hodisaWS.onclose = function() {
    document.getElementById('ws-holat').textContent = 'Uzildi';
    document.getElementById('ws-holat').className = 'badge qizil';
    setTimeout(hodisaWSUlash, 3000);
  };
}

// ── Jadval ────────────────────────────────────
function vaqtFormat(v) {
  if (!v) return '—';
  return v.replace('T', ' ').substring(0, 16);
}

function harakatBadge(harakat) {
  if (harakat === 'kirdi')  return '<span class="harakat-kirdi">&#9654; Kirdi</span>';
  if (harakat === 'chiqdi') return '<span class="harakat-chiqdi">&#9664; Chiqdi</span>';
  return harakat || '—';
}

function transportJadvalQoshish(d, yangi) {
  const tbody = document.getElementById('transport-tbody');
  if (!tbody) return;
  const bosh = tbody.querySelector('.bosh');
  if (bosh) bosh.parentElement.remove();
  const tr = document.createElement('tr');
  if (yangi) tr.classList.add('yangi');
  tr.innerHTML =
    '<td>' + vaqtFormat(d.vaqt) + '</td>' +
    '<td><strong>' + (d.raqam || '—') + '</strong></td>' +
    '<td>' + (d.tur || '—') + '</td>' +
    '<td>' + (d.rang || '—') + '</td>' +
    '<td>' + (d.davlat || '—') + '</td>' +
    '<td>' + (d.viloyat || '—') + '</td>' +
    '<td>' + harakatBadge(d.harakat) + '</td>';
  tbody.insertBefore(tr, tbody.firstChild);
  while (tbody.children.length > 100) tbody.removeChild(tbody.lastChild);
}

function ishchiJadvalQoshish(d, yangi) {
  const tbody = document.getElementById('ishchi-tbody');
  if (!tbody) return;
  const bosh = tbody.querySelector('.bosh');
  if (bosh) bosh.parentElement.remove();
  const tr = document.createElement('tr');
  if (yangi) tr.classList.add('yangi');
  tr.innerHTML =
    '<td>' + vaqtFormat(d.vaqt) + '</td>' +
    '<td><strong>' + (d.ism || "Noma'lum") + '</strong></td>' +
    '<td>' + harakatBadge(d.harakat) + '</td>';
  tbody.insertBefore(tr, tbody.firstChild);
  while (tbody.children.length > 100) tbody.removeChild(tbody.lastChild);
}

// ── Hodisalar lenta ───────────────────────────
function hodisaQoshish(tur, d) {
  const lenta = document.getElementById('hodisalar-lenta');
  if (!lenta) return;
  const div = document.createElement('div');
  div.className = 'hodisa ' + tur;
  const vaqt = new Date().toLocaleTimeString('uz');
  if (tur === 'transport') {
    div.innerHTML = '<strong>' + vaqt + '</strong> — ' +
      (d.tur || 'Transport') + ' <strong>' + (d.raqam || '') + '</strong> ' +
      (d.harakat === 'kirdi' ? 'KIRDI' : 'CHIQDI') + ' | ' +
      (d.rang || '') + ' | ' + (d.davlat || '') + '/' + (d.viloyat || '');
  } else if (tur === 'ishchi') {
    div.innerHTML = '<strong>' + vaqt + '</strong> — ' +
      '<strong>' + (d.ism || "Noma'lum") + '</strong> aniqlandi';
  } else {
    div.innerHTML = '<strong>' + vaqt + '</strong> — ' + (d.harakat || '');
  }
  lenta.insertBefore(div, lenta.firstChild);
  while (lenta.children.length > 50) lenta.removeChild(lenta.lastChild);
}

// ── Statistika ────────────────────────────────
async function statistikaYangilash() {
  try {
    const r = await fetch('/api/statistika');
    const d = await r.json();
    document.getElementById('bugun-kirdi').textContent   = (d.bugun_transport && d.bugun_transport['kirdi'])   || 0;
    document.getElementById('bugun-chiqdi').textContent  = (d.bugun_transport && d.bugun_transport['chiqdi'])  || 0;
    document.getElementById('bugun-ishchi').textContent  = d.bugun_ishchilar  || 0;
    document.getElementById('jami-transport').textContent = d.jami_transport  || 0;
  } catch(e) {
    console.warn('[Statistika] Xatolik:', e);
  }
}

// ── Ma'lumotlar yuklash ───────────────────────
async function malumotlarYuklash() {
  try {
    const tr = await fetch('/api/transport?limit=50').then(function(r){ return r.json(); });
    const ir = await fetch('/api/ishchilar?limit=50').then(function(r){ return r.json(); });
    tr.forEach(function(d){ transportJadvalQoshish(d, false); });
    ir.forEach(function(d){ ishchiJadvalQoshish(d, false); });
  } catch(e) {
    console.warn('[Malumot] Xatolik:', e);
  }
}

// ── Tugmalar ─────────────────────────────────
async function transportSkan(harakat) {
  xabarKorsatish('Skaplanmoqda...', 'muvaffaq');
  try {
    const r = await fetch('/api/transport/' + harakat, { method: 'POST' });
    const d = await r.json();
    if (d.holat === 'ok') {
      const m = d.malumot;
      xabarKorsatish(
        (m.tur || '') + ' ' + harakat.toUpperCase() + ': ' +
        (m.raqam || '') + ' | ' + (m.rang || '') + ' | ' +
        (m.davlat || '') + '/' + (m.viloyat || ''),
        'muvaffaq'
      );
      transportDetalKorsatish(m);
      transportJadvalQoshish(Object.assign({}, m, { vaqt: new Date().toISOString() }), true);
      statistikaYangilash();
    } else {
      xabarKorsatish('Xatolik: ' + (d.xabar || 'Noma\'lum'), 'xato');
    }
  } catch(e) {
    xabarKorsatish('Server bilan bog\'lanishda xatolik', 'xato');
  }
}

async function ishchiSkan() {
  xabarKorsatish('Ishchilar skaplanmoqda...', 'muvaffaq');
  try {
    const r = await fetch('/api/ishchi/skan', { method: 'POST' });
    const d = await r.json();
    if (d.son > 0) {
      xabarKorsatish(d.son + ' ta ishchi aniqlandi', 'muvaffaq');
      d.ishchilar.forEach(function(i) {
        ishchiJadvalQoshish({ ism: i.ism, harakat: 'aniqlandi', vaqt: new Date().toISOString() }, true);
      });
      tabAlmash('ishchi');
      statistikaYangilash();
    } else {
      xabarKorsatish('Ishchi topilmadi', 'muvaffaq');
    }
  } catch(e) {
    xabarKorsatish('Xatolik: ' + e.message, 'xato');
  }
}

function excelYuklash() {
  const tanlangan = prompt(
    'Qaysi davr uchun Excel hisobot?\n\n1 - Bugun\n2 - Bu hafta\n3 - Bu oy\n4 - Hammasi\n\nRaqam kiriting (1-4):',
    '1'
  );
  const davrlar = { '1': 'bugun', '2': 'hafta', '3': 'oy', '4': 'hammasi' };
  const davr = davrlar[tanlangan];
  if (!davr) { xabarKorsatish("Noto'g'ri tanlov", 'xato'); return; }
  xabarKorsatish('Excel tayyorlanmoqda...', 'muvaffaq');
  window.open('/api/excel/yuklash?davr=' + davr, '_blank');
}

function pdfYuklash() {
  const tanlangan = prompt(
    'Qaysi davr uchun PDF hisobot?\n\n1 - Bugun\n2 - Bu hafta\n3 - Bu oy\n4 - Hammasi\n\nRaqam kiriting (1-4):',
    '1'
  );
  const davrlar = { '1': 'bugun', '2': 'hafta', '3': 'oy', '4': 'hammasi' };
  const davr = davrlar[tanlangan];
  if (!davr) { xabarKorsatish("Noto'g'ri tanlov", 'xato'); return; }
  xabarKorsatish('PDF tayyorlanmoqda...', 'muvaffaq');
  window.open('/api/pdf/yuklash?davr=' + davr, '_blank');
}

// ── Yordamchi ────────────────────────────────
function xabarKorsatish(matn, tur) {
  const el = document.getElementById('natija-xabar');
  if (!el) return;
  el.textContent = matn;
  el.className = 'natija-xabar ' + (tur || 'muvaffaq');
  el.style.display = 'block';
  clearTimeout(el._timer);
  el._timer = setTimeout(function(){ el.style.display = 'none'; }, 5000);
}

function transportDetalKorsatish(d) {
  const karta = document.getElementById('oxirgi-transport-karta');
  const detal = document.getElementById('transport-detal');
  if (!karta || !detal) return;
  karta.style.display = 'block';
  const maydonlar = [
    ['Raqam',   d.raqam],
    ['Tur',     d.tur],
    ['Rang',    d.rang],
    ['Davlat',  d.davlat],
    ['Viloyat', d.viloyat],
    ['Harakat', d.harakat === 'kirdi' ? 'KIRDI' : 'CHIQDI'],
    ['Ishonch', d.ishonch ? Math.round(d.ishonch * 100) + '%' : '—'],
    ['Rasm',    d.rasm_yol ? 'Saqlandi' : "Yo'q"],
  ];
  detal.innerHTML = maydonlar.map(function(item) {
    return '<div class="detal-qator"><div class="detal-nom">' + item[0] +
           '</div><div class="detal-qiy">' + (item[1] || '—') + '</div></div>';
  }).join('');
}

function tabAlmash(nom) {
  document.getElementById('panel-transport').style.display = nom === 'transport' ? 'block' : 'none';
  document.getElementById('panel-ishchi').style.display   = nom === 'ishchi'     ? 'block' : 'none';
  document.getElementById('tab-transport').className = 'tab' + (nom === 'transport' ? ' faol' : '');
  document.getElementById('tab-ishchi').className    = 'tab' + (nom === 'ishchi'    ? ' faol' : '');
}

// ── Ishga tushirish ───────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  malumotlarYuklash();
  statistikaYangilash();
  videoWSUlash();
  hodisaWSUlash();
  setInterval(statistikaYangilash, 30000);
  hodisaQoshish('info', { harakat: 'Tizim ishga tushdi' });
  console.log('[App] Zavod Monitoring ishga tushdi');
});
