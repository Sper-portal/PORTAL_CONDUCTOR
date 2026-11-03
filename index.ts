// Portal del Conductor · función «deportes» (Supabase Edge Function, Deno). Un solo archivo.
//
// Qué hace: pide a Football-Data (LaLiga y Champions) y, si se activa, a la API de la Euroliga los partidos,
// clasificaciones y equipos, y los GUARDA en la tabla sports_cache. La app solo habla con esta función.
//   - Las claves están en los «Secrets» de Supabase (FOOTBALL_DATA_KEY). No salen nunca de aquí.
//   - Da igual cuántos móviles pregunten: a la web de fuera solo se llama cuando la caché caduca (y solo una vez a la vez).
//   - Tope propio de llamadas por minuto (Football-Data gratis permite 10; aquí 5) y respeto de «demasiadas peticiones» (429).
//   - Si la fuente falla, se devuelve lo último guardado marcado como «stale» (no se rompe la pantalla).
//
// Rutas (GET):  ?r=matches | standings&c=PD | teams&c=PD | competitions | diag
// Secrets:      FOOTBALL_DATA_KEY (obligatorio)   EUROLEAGUE=on (opcional: activa el baloncesto, mirar primero ?r=diag)
// Automáticos:  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

const VERSION = 'deportes-1';
const TZ = 'Europe/Madrid';
const FD = 'https://api.football-data.org/v4';
const EL = 'https://api-live.euroleague.net';
const FD_PER_MIN = 5;                       // el plan gratis de Football-Data permite 10 por minuto
const CAL = ['PD', 'CL'];                   // competiciones del calendario (LaLiga y Champions)
const FREE: Record<string, string> = {      // las 12 del plan gratis de Football-Data
  PD: 'LaLiga', CL: 'Champions League', PL: 'Premier League', BL1: 'Bundesliga', SA: 'Serie A', FL1: 'Ligue 1',
  DED: 'Eredivisie', PPL: 'Primeira Liga', ELC: 'Championship', BSA: 'Brasileirão Série A', WC: 'Mundial', EC: 'Eurocopa',
};

// «ahora» y «fetch» se pueden cambiar en las pruebas
const deps = { now: () => Date.now() };

const CORS: Record<string, string> = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': 'authorization, apikey, content-type, x-client-info',
  'access-control-allow-methods': 'GET, OPTIONS',
};

function out(body: unknown, status = 200, maxAge = 0): Response {
  const h: Record<string, string> = { ...CORS, 'content-type': 'application/json; charset=utf-8' };
  if (maxAge > 0) h['cache-control'] = 'public, max-age=' + maxAge;
  return new Response(JSON.stringify(body), { status, headers: h });
}

// ---------------------------------------------------------------- fechas (hora de Madrid)
function ymd(ms: number): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(ms));
}
function hm(ms: number): string {
  return new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(ms)).replace(/^24:/, '00:');
}
function addDays(d: string, n: number): string {
  const p = d.split('-').map(Number);
  return new Date(Date.UTC(p[0], p[1] - 1, p[2] + n)).toISOString().slice(0, 10);
}
function esc(s: string): string {
  return s.replace(/[^\w.:-]/g, '_');
}

// ---------------------------------------------------------------- base de datos (PostgREST con la clave de servicio)
function env(k: string): string {
  try { return (Deno.env.get(k) || '').trim(); } catch (_e) { return ''; }
}
function dbh(extra?: Record<string, string>): Record<string, string> {
  const k = env('SUPABASE_SERVICE_ROLE_KEY');
  return { apikey: k, authorization: 'Bearer ' + k, 'content-type': 'application/json', ...(extra || {}) };
}
function dbu(q: string): string {
  return env('SUPABASE_URL').replace(/\/+$/, '') + '/rest/v1/sports_cache' + q;
}
type Row = { key: string; payload: any; fetched_at: string; ttl_s: number };

async function dbGet(key: string): Promise<Row | null> {
  const r = await fetch(dbu('?select=*&key=eq.' + encodeURIComponent(key)), { headers: dbh(), signal: AbortSignal.timeout(6000) });
  if (!r.ok) throw new Error('bd ' + r.status);
  const a = await r.json();
  return Array.isArray(a) && a.length ? a[0] : null;
}
async function dbPut(key: string, payload: unknown, ttl: number): Promise<void> {
  const r = await fetch(dbu('?on_conflict=key'), {
    method: 'POST', headers: dbh({ prefer: 'resolution=merge-duplicates,return=minimal' }), signal: AbortSignal.timeout(6000),
    body: JSON.stringify({ key, payload, ttl_s: Math.round(ttl), fetched_at: new Date(deps.now()).toISOString() }),
  });
  if (!r.ok) throw new Error('bd ' + r.status);
}
async function dbDel(q: string): Promise<void> {
  await fetch(dbu(q), { method: 'DELETE', headers: dbh(), signal: AbortSignal.timeout(6000) }).catch(() => {});
}
// Cerrojo: solo uno a la vez refresca una misma clave (aunque haya varias copias de la función)
async function lock(name: string, secs: number): Promise<boolean> {
  const key = 'lock:' + name;
  for (let i = 0; i < 2; i++) {
    const r = await fetch(dbu('?on_conflict=key'), {
      method: 'POST', headers: dbh({ prefer: 'resolution=ignore-duplicates,return=representation' }), signal: AbortSignal.timeout(6000),
      body: JSON.stringify({ key, payload: { until: deps.now() + secs * 1000 }, ttl_s: secs, fetched_at: new Date(deps.now()).toISOString() }),
    });
    if (!r.ok) throw new Error('bd ' + r.status);
    const a = await r.json();
    if (Array.isArray(a) && a.length) return true;
    const cur = await dbGet(key);
    if (cur && cur.payload && Number(cur.payload.until) > deps.now()) return false;
    await dbDel('?key=eq.' + encodeURIComponent(key));          // cerrojo viejo: se quita y se reintenta
  }
  return false;
}
async function unlock(name: string): Promise<void> {
  await dbDel('?key=eq.' + encodeURIComponent('lock:' + name));
}
// Limpieza de filas viejas (de vez en cuando)
async function prune(): Promise<void> {
  await dbDel('?fetched_at=lt.' + encodeURIComponent(new Date(deps.now() - 3 * 86400000).toISOString()) + '&key=not.like.' + encodeURIComponent('rate:*') + '&key=not.like.' + encodeURIComponent('block:*'));
}

// ---------------------------------------------------------------- tope de llamadas y bloqueo por 429 (solo Football-Data)
async function fdAllowed(): Promise<{ ok: boolean; why?: string }> {
  const b = await dbGet('block:fd');
  if (b && b.payload && Number(b.payload.until) > deps.now()) return { ok: false, why: 'bloqueo' };
  const r = await dbGet('rate:fd');
  const m = Math.floor(deps.now() / 60000);
  if (r && r.payload && r.payload.m === m && Number(r.payload.n) >= FD_PER_MIN) return { ok: false, why: 'cuota' };
  return { ok: true };
}
async function fdCount(): Promise<void> {
  const m = Math.floor(deps.now() / 60000);
  let n = 0;
  try { const r = await dbGet('rate:fd'); if (r && r.payload && r.payload.m === m) n = Number(r.payload.n) || 0; } catch (_e) { /* sigue */ }
  await dbPut('rate:fd', { m, n: n + 1 }, 120).catch(() => {});
}
class Upstream extends Error {
  status: number;
  constructor(msg: string, status: number) { super(msg); this.status = status; }
}
async function fdGet(path: string): Promise<any> {
  const key = env('FOOTBALL_DATA_KEY');
  if (!key) throw new Upstream('sin_clave', 0);
  const al = await fdAllowed();
  if (!al.ok) throw new Upstream(al.why || 'cuota', 0);
  await fdCount();
  const r = await fetch(FD + path, { headers: { 'X-Auth-Token': key }, signal: AbortSignal.timeout(8000) });
  if (r.status === 429) {
    const ra = Number(r.headers.get('retry-after')) || 60;
    await dbPut('block:fd', { until: deps.now() + ra * 1000 }, ra).catch(() => {});
    throw new Upstream('429', 429);
  }
  if (r.status === 403) throw new Upstream('403', 403);   // el plan gratis no incluye eso
  if (!r.ok) throw new Upstream('http ' + r.status, r.status);
  return await r.json();
}

// ---------------------------------------------------------------- caché con ttl, cerrojo y «stale»
type Got = { data: any; fresh: boolean; age: number; ttl: number; stale?: boolean; err?: string };
async function cached(key: string, fetcher: () => Promise<any>, ttlOf: (d: any) => number): Promise<Got> {
  const now = deps.now();
  let row: Row | null = null;
  try { row = await dbGet(key); } catch (_e) { throw new Upstream('sin_tabla', 0); }   // sin base de datos no se llama fuera (se gastaría la cuota sin guardar nada)
  const age = (r: Row) => Math.max(0, Math.round((now - Date.parse(r.fetched_at)) / 1000));
  if (row && age(row) < row.ttl_s) return { data: row.payload, fresh: true, age: age(row), ttl: row.ttl_s };
  let have = false;
  try { have = await lock(key, 20); } catch (_e) { have = false; }
  if (!have) {
    if (row) return { data: row.payload, fresh: false, age: age(row), ttl: row.ttl_s, stale: true, err: 'actualizando' };
    for (let i = 0; i < 6; i++) {                           // otro lo está pidiendo: esperamos un poco
      await new Promise((ok) => setTimeout(ok, 700));
      try { const r2 = await dbGet(key); if (r2) return { data: r2.payload, fresh: true, age: age(r2), ttl: r2.ttl_s }; } catch (_e) { /* sigue */ }
    }
    throw new Upstream('ocupado', 0);
  }
  try {
    try {                                                   // quizá otro la acaba de refrescar mientras esperábamos el cerrojo
      const r3 = await dbGet(key);
      if (r3 && Math.max(0, Math.round((deps.now() - Date.parse(r3.fetched_at)) / 1000)) < r3.ttl_s) return { data: r3.payload, fresh: true, age: age(r3), ttl: r3.ttl_s };
    } catch (_e) { /* sigue */ }
    const d = await fetcher();
    const ttl = Math.max(60, Math.round(ttlOf(d)));
    await dbPut(key, d, ttl);
    if (Math.random() < 0.02) await prune();
    return { data: d, fresh: true, age: 0, ttl };
  } catch (e) {
    if (row) return { data: row.payload, fresh: false, age: age(row), ttl: row.ttl_s, stale: true, err: e instanceof Upstream ? e.message : 'fallo' };
    throw e;
  } finally {
    await unlock(key);
  }
}

// ---------------------------------------------------------------- fútbol (Football-Data)
const MAD: Array<[RegExp, string, string]> = [   // clubes de Madrid capital: su estadio (para «Madrid hoy»)
  [/real madrid/i, 'Santiago Bernabéu', 'Madrid'],
  [/atl[eé]tico (de )?madrid/i, 'Riyadh Air Metropolitano', 'Madrid'],
  [/rayo vallecano/i, 'Estadio de Vallecas', 'Madrid'],
];
function madVenue(t: any): [string, string] | null {
  const n = String((t && (t.name || t.shortName)) || '');
  for (const m of MAD) if (m[0].test(n)) return [m[1], m[2]];
  return null;
}
function fdStatus(s: string): string {
  s = String(s || '').toUpperCase();
  if (s === 'IN_PLAY' || s === 'LIVE') return 'vivo';
  if (s === 'PAUSED') return 'desc';
  if (s === 'FINISHED' || s === 'AWARDED') return 'fin';
  if (s === 'POSTPONED' || s === 'SUSPENDED') return 'apl';
  if (s === 'CANCELLED' || s === 'CANCELED') return 'canc';
  return 'prog';
}
function num(x: any): number | null {
  return typeof x === 'number' && isFinite(x) ? x : null;
}
function team(t: any): any {
  t = t || {};
  return { id: t.id == null ? null : t.id, n: String(t.shortName || t.name || '—'), tla: String(t.tla || ''), crest: String(t.crest || t.crestUrl || '') };
}
function normFd(m: any): any | null {
  if (!m || !m.utcDate) return null;
  const u = Date.parse(m.utcDate);
  if (!isFinite(u)) return null;
  const ft = (m.score && m.score.fullTime) || {};
  const home = m.homeTeam || {};
  const mv = madVenue(home);
  const o: any = {
    id: 'fd' + m.id, sp: 'f', c: String((m.competition && m.competition.code) || ''), cn: String((m.competition && (FREE[m.competition.code] || m.competition.name)) || ''),
    u: new Date(u).toISOString(), d: ymd(u), t: hm(u), s: fdStatus(m.status),
    min: num(m.minute), h: team(m.homeTeam), a: team(m.awayTeam),
    hs: num(ft.home != null ? ft.home : ft.homeTeam), as: num(ft.away != null ? ft.away : ft.awayTeam),
    v: mv ? mv[0] : String(m.venue || ''), ci: mv ? mv[1] : '', md: num(m.matchday),
  };
  if (mv) o.mad = 1;
  return o;
}
function ttlMatches(list: any[]): number {
  const now = deps.now();
  let next: number | null = null;
  for (const m of list) {
    const u = Date.parse(m.u);
    if (m.s === 'vivo' || m.s === 'desc') return 120;
    if ((m.s === 'prog') && u <= now && now - u < 3 * 3600000) return 120;         // debería estar jugándose: la fuente va con retraso
    if (m.s === 'prog' && u > now && (next == null || u < next)) next = u;
  }
  if (next == null) return 3600;
  const secs = (next - now) / 1000;
  if (secs <= 900) return 300;
  return Math.min(3600, Math.max(60, secs - 120));
}
async function fdMatches(today: string): Promise<any> {
  const from = addDays(today, -1), to = addDays(today, 7);
  const j = await fdGet('/matches?dateFrom=' + from + '&dateTo=' + to + '&competitions=' + CAL.join(','));
  const L = (j && Array.isArray(j.matches)) ? j.matches : null;
  if (!L) throw new Upstream('respuesta no válida', 0);
  const lo = from, hi = addDays(today, 6);
  const f = L.map(normFd).filter((m: any) => m && m.d >= lo && m.d <= hi);
  f.sort((a: any, b: any) => (a.u < b.u ? -1 : a.u > b.u ? 1 : 0));
  return f;
}

// ---------------------------------------------------------------- baloncesto (Euroliga) — solo si EUROLEAGUE=on
function elOn(): boolean {
  return env('EUROLEAGUE').toLowerCase() === 'on';
}
function pickStr(o: any, ks: string[]): string {
  for (const k of ks) { const v = o && o[k]; if (typeof v === 'string' && v) return v; }
  return '';
}
function elTeam(t: any): any {
  if (typeof t === 'string') return { id: null, n: t, tla: '', crest: '' };
  t = t || {};
  return { id: t.code || t.id || null, n: pickStr(t, ['name', 'clubName', 'teamName', 'shortName', 'tvCode']) || '—', tla: pickStr(t, ['code', 'tvCode', 'abbreviatedName']), crest: pickStr(t, ['imageUrl', 'logo', 'crest']) };
}
// Fechas sin zona horaria («2026-11-05T20:45:00»): se interpretan como hora de Madrid (la web de la Euroliga enseña CET).
function elTime(s: string): number | null {
  if (!s) return null;
  if (/[zZ]$|[+-]\d\d:?\d\d$/.test(s)) { const t = Date.parse(s); return isFinite(t) ? t : null; }
  const m = /^(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d)/.exec(s);
  if (!m) return null;
  const guess = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
  for (const off of [3600000, 7200000]) {                   // invierno (+1) o verano (+2): el que dé esa misma hora en Madrid
    const t = guess - off;
    if (hm(t) === m[4] + ':' + m[5] && ymd(t) === m[1] + '-' + m[2] + '-' + m[3]) return t;
  }
  return guess - 3600000;
}
function elNorm(g: any): any | null {
  if (!g || typeof g !== 'object') return null;
  const t = elTime(pickStr(g, ['utcDate', 'date', 'startDate', 'gameDate', 'dateTime', 'startTime']));
  if (t == null) return null;
  const h = elTeam(g.home || g.homeTeam || g.local || g.homeClub || pickStr(g, ['homeTeamName', 'localTeam']));
  const a = elTeam(g.away || g.awayTeam || g.road || g.awayClub || pickStr(g, ['awayTeamName', 'roadTeam']));
  const hs = num((g.home && g.home.score) != null ? g.home.score : (g.homeScore != null ? g.homeScore : g.homeTeamScore));
  const as = num((g.away && g.away.score) != null ? g.away.score : (g.awayScore != null ? g.awayScore : g.awayTeamScore));
  const played = g.played === true || String(g.status || '').toLowerCase() === 'finished';
  const live = String(g.status || '').toLowerCase() === 'live' || g.live === true;
  const venue = typeof g.venue === 'string' ? g.venue : pickStr(g.venue || g.arena || {}, ['name']);
  const real = /real madrid/i.test(h.n);
  const o: any = {
    id: 'el' + String(g.gameCode || g.code || g.id || (ymd(t) + h.n)), sp: 'b', c: 'EL', cn: 'Euroliga',
    u: new Date(t).toISOString(), d: ymd(t), t: hm(t), s: live ? 'vivo' : (played ? 'fin' : 'prog'),
    min: null, h, a, hs: played || live ? hs : null, as: played || live ? as : null,
    v: real ? 'Movistar Arena' : venue, ci: real ? 'Madrid' : '', md: num(g.round || g.gameday || g.matchday),
  };
  if (real) o.mad = 1;
  return o;
}
function elSeasonCode(now: number): string {
  const y = Number(ymd(now).slice(0, 4)), m = Number(ymd(now).slice(5, 7));
  return 'E' + (m >= 7 ? y : y - 1);
}
async function elGet(path: string): Promise<any> {
  const r = await fetch(EL + path, { headers: { accept: 'application/json' }, signal: AbortSignal.timeout(8000) });
  if (!r.ok) throw new Upstream('http ' + r.status, r.status);
  return await r.json();
}
async function elMatches(today: string): Promise<any> {
  const j = await elGet('/v2/competitions/E/seasons/' + elSeasonCode(deps.now()) + '/games');
  const L = Array.isArray(j) ? j : (j && (j.data || j.games || j.items || j.results));
  if (!Array.isArray(L)) throw new Upstream('respuesta no válida', 0);
  const lo = addDays(today, -1), hi = addDays(today, 6);
  const f = L.map(elNorm).filter((m: any) => m && m.d >= lo && m.d <= hi);
  f.sort((a: any, b: any) => (a.u < b.u ? -1 : a.u > b.u ? 1 : 0));
  return f;
}

// ---------------------------------------------------------------- rutas
function meta(r: string, g: Got, extra?: any): any {
  const o: any = { ok: true, v: VERSION, r, gen: new Date(deps.now()).toISOString(), age: g.age, ttl: g.ttl, fresh: g.fresh };
  if (g.stale) { o.stale = true; if (g.err) o.err = g.err; }
  return { ...o, ...(extra || {}) };
}
function fail(r: string, e: unknown): Response {
  const m = e instanceof Upstream ? e.message : 'fallo';
  return out({ ok: false, v: VERSION, r, err: m, gen: new Date(deps.now()).toISOString() });
}

async function routeMatches(): Promise<Response> {
  const today = ymd(deps.now());
  let f: any[] = [], b: any[] = [], g: Got | null = null, ferr = '', berr = '';
  try {
    g = await cached('football:matches:' + today, () => fdMatches(today), ttlMatches);
    f = g.data;
  } catch (e) { ferr = e instanceof Upstream ? e.message : 'fallo'; }
  let gb: Got | null = null;
  if (elOn()) {
    try { gb = await cached('basket:matches:' + today, () => elMatches(today), ttlMatches); b = gb.data; }
    catch (e) { berr = e instanceof Upstream ? e.message : 'fallo'; }
  }
  if (!g && !gb) return out({ ok: false, v: VERSION, r: 'matches', err: ferr || berr || 'fallo', gen: new Date(deps.now()).toISOString() });
  const base: Got = g || gb!;
  const ttl = Math.min(g ? g.ttl : 3600, gb ? gb.ttl : 3600);
  const o = meta('matches', { ...base, ttl, fresh: (g ? g.fresh : true) && (gb ? gb.fresh : true), stale: (g && g.stale) || (gb && gb.stale) || false, age: Math.max(g ? g.age : 0, gb ? gb.age : 0), err: ferr || berr || base.err },
    { today, bk: elOn(), f, b, ferr: ferr || undefined, berr: berr || undefined, note: 'Football-Data gratis: los marcadores llegan con retraso' });
  return out(o, 200, 20);
}

async function routeStandings(c: string): Promise<Response> {
  if (!FREE[c]) return out({ ok: false, err: 'competición no válida' }, 400);
  try {
    const g = await cached('football:standings:' + c, async () => {
      const j = await fdGet('/competitions/' + c + '/standings');
      const S = j && Array.isArray(j.standings) ? j.standings : null;
      if (!S) throw new Upstream('respuesta no válida', 0);
      const tot = S.find((s: any) => s.type === 'TOTAL') || S[0];
      const rows = ((tot && tot.table) || []).map((r: any) => ({
        p: num(r.position), t: team(r.team), pj: num(r.playedGames), g: num(r.won), e: num(r.draw), pe: num(r.lost),
        gf: num(r.goalsFor), gc: num(r.goalsAgainst), dg: num(r.goalDifference), pts: num(r.points),
      }));
      return { c, cn: FREE[c], season: j.season && j.season.currentMatchday != null ? j.season.currentMatchday : null, rows };
    }, () => 10800);
    return out(meta('standings', g, { c, data: g.data }), 200, 60);
  } catch (e) { return fail('standings', e); }
}

async function routeTeams(c: string): Promise<Response> {
  if (!FREE[c]) return out({ ok: false, err: 'competición no válida' }, 400);
  try {
    const g = await cached('football:teams:' + c, async () => {
      const j = await fdGet('/competitions/' + c + '/teams');
      const T = j && Array.isArray(j.teams) ? j.teams : null;
      if (!T) throw new Upstream('respuesta no válida', 0);
      return { c, cn: FREE[c], teams: T.map((t: any) => ({ ...team(t), v: String(t.venue || ''), fo: num(t.founded) })) };
    }, () => 7 * 86400);
    return out(meta('teams', g, { c, data: g.data }), 200, 300);
  } catch (e) { return fail('teams', e); }
}

function routeCompetitions(): Response {
  const list = Object.keys(FREE).map((c) => ({ c, n: FREE[c], cal: CAL.indexOf(c) >= 0, sp: 'f' }));
  if (elOn()) list.push({ c: 'EL', n: 'Euroliga', cal: true, sp: 'b' });
  return out({ ok: true, v: VERSION, r: 'competitions', bk: elOn(), data: list,
    nota: 'Football-Data (plan gratis): estas 12. Faltan Copa del Rey, Europa League y Segunda. Los marcadores van con retraso.' }, 200, 3600);
}

async function routeDiag(): Promise<Response> {
  try {
    const g = await cached('diag', async () => {
      const o: any = { fd: { key: !!env('FOOTBALL_DATA_KEY') }, el: { on: elOn() }, bd: true };
      try {
        const j = await fdGet('/competitions');
        o.fd.ok = true; o.fd.n = Array.isArray(j.competitions) ? j.competitions.length : null;
        o.fd.codes = Array.isArray(j.competitions) ? j.competitions.map((c: any) => c.code).slice(0, 20) : null;
      } catch (e) { o.fd.ok = false; o.fd.err = e instanceof Upstream ? e.message : 'fallo'; }
      try {
        const r = await fetch(EL + '/v2/competitions/E/seasons/' + elSeasonCode(deps.now()) + '/games', { headers: { accept: 'application/json' }, signal: AbortSignal.timeout(8000) });
        const t = await r.text();
        o.el.status = r.status; o.el.ctype = r.headers.get('content-type') || ''; o.el.muestra = t.slice(0, 900);
      } catch (e) { o.el.err = 'sin respuesta'; }
      return o;
    }, () => 600);
    return out(meta('diag', g, { data: g.data }));
  } catch (e) { return fail('diag', e); }
}

export async function handle(req: Request): Promise<Response> {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (req.method !== 'GET') return out({ ok: false, err: 'método no permitido' }, 405);
  if (!env('SUPABASE_URL') || !env('SUPABASE_SERVICE_ROLE_KEY')) return out({ ok: false, err: 'sin_bd' });
  const q = new URL(req.url).searchParams;
  const r = q.get('r') || '';
  const c = esc((q.get('c') || '').toUpperCase());
  try {
    if (r === 'matches') return await routeMatches();
    if (r === 'standings') return await routeStandings(c || 'PD');
    if (r === 'teams') return await routeTeams(c || 'PD');
    if (r === 'competitions') return routeCompetitions();
    if (r === 'diag') return await routeDiag();
  } catch (e) { return fail(r, e); }
  return out({ ok: false, err: 'ruta no válida', rutas: ['matches', 'standings', 'teams', 'competitions', 'diag'] }, 400);
}

export const __deps = deps;
Deno.serve((req: Request) => handle(req));
