"use strict";
/* CargoBox · interfaz web. JS simple, sin dependencias. Se refresca sola cada 6 s (tiempo real). */

const $ = (s, r = document) => r.querySelector(s);
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const dinero = (t) => t?.texto || "";
const fecha = (iso) => (iso ? new Date(iso).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" }) : "");

const INSTALACIONES = ["CD Monterrey", "CD Saltillo", "CD Guadalajara", "CD Ciudad de México", "CD Reynosa"];
const FLUJO = ["RECIBIDO", "CLASIFICADO", "EN_TRANSITO", "CENTRO_DESTINO", "EN_REPARTO", "ENTREGADO"];
const NOMBRE_PASO = { RECIBIDO: "Recibido", CLASIFICADO: "Clasificado", EN_TRANSITO: "En tránsito", CENTRO_DESTINO: "Centro destino", EN_REPARTO: "En reparto", ENTREGADO: "Entregado" };
const MENSAJE = {
  RECIBIDO: "Ya tenemos tu paquete en sucursal. Pronto saldrá a clasificación.",
  CLASIFICADO: "Tu paquete fue clasificado y se prepara para el viaje.",
  EN_TRANSITO: "Tu paquete va en camino entre ciudades.",
  CENTRO_DESTINO: "Tu paquete llegó a la ciudad de destino y pronto saldrá a reparto.",
  EN_REPARTO: "¡Hoy puede llegar! El repartidor lo lleva en su unidad.",
  ENTREGADO: "Entregado y comprobado con firma o foto.",
  SEGUNDO_INTENTO_PENDIENTE: "No hubo quien recibiera. Reprogramamos un nuevo intento de entrega.",
  RETENIDO_EN_SUCURSAL: "No se pudo entregar tras varios intentos. Te esperamos en sucursal.",
  DIRECCION_INCORRECTA: "No encontramos la dirección. Atención al cliente se pondrá en contacto para corregirla.",
  RETENIDO_POR_INCIDENCIA: "Hubo una incidencia con el paquete. Atención al cliente lo está revisando.",
  RECHAZADO_EN_DEVOLUCION: "El destinatario rechazó el paquete; regresa a la sucursal de origen.",
  DEVUELTO_A_ORIGEN: "El paquete ya regresó a la sucursal de origen.",
  CANCELADO: "Este envío fue cancelado.",
};
const clase = (e) => (["ENTREGADO", "DEVUELTO_A_ORIGEN"].includes(e) ? "ok" : ["DIRECCION_INCORRECTA", "RETENIDO_POR_INCIDENCIA", "RECHAZADO_EN_DEVOLUCION", "CANCELADO"].includes(e) ? "bad" : ["SEGUNDO_INTENTO_PENDIENTE", "RETENIDO_EN_SUCURSAL"].includes(e) ? "warn" : "");
const chip = (p) => `<span class="chip ${clase(p.estado)}">${esc(p.estado_etiqueta)}</span>`;

/* ---------------------------------------------------------------- API y avisos */
async function api(ruta, metodo = "GET", cuerpo) {
  const r = await fetch("/api/v1" + ruta, { method: metodo, headers: { "Content-Type": "application/json" }, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos?.error?.mensaje || "No se pudo completar la acción");
  return datos;
}
function aviso(texto, tipo = "ok") {
  const t = document.createElement("div");
  t.className = "toast " + tipo;
  t.textContent = texto;
  $("#toasts").append(t);
  setTimeout(() => t.remove(), 5000);
}
async function intentar(fn, ok) {
  try { const r = await fn(); if (ok) aviso(ok); await refrescar(); return r; }
  catch (e) { aviso(e.message, "err"); }
}

/* ---------------------------------------------------------------- navegación */
let pestaña = "rastreo";
let paquetes = [];
function ir(tab) {
  pestaña = tab;
  document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  document.querySelectorAll(".tab").forEach((s) => s.classList.toggle("on", s.id === "tab-" + tab));
  refrescar();
}
$("#nav").addEventListener("click", (e) => e.target.dataset.tab && ir(e.target.dataset.tab));

/* ---------------------------------------------------------------- tablas reutilizables */
function tabla(contenedor, lista, columnas, { seleccion = false, acciones = null, vacio = "Nada por aquí por ahora." } = {}) {
  const c = typeof contenedor === "string" ? $(contenedor) : contenedor;
  if (!lista.length) { c.innerHTML = `<div class="empty">${esc(vacio)}</div>`; return; }
  const cab = (seleccion ? "<th></th>" : "") + columnas.map((x) => `<th>${esc(x[0])}</th>`).join("") + (acciones ? "<th></th>" : "");
  const filas = lista.map((p, i) => `<tr data-i="${i}">` + (seleccion ? `<td><input type="checkbox" class="sel" value="${esc(p.guia)}"></td>` : "")
    + columnas.map((x) => `<td>${x[1](p)}</td>`).join("") + (acciones ? `<td class="btns">${acciones(p)}</td>` : "") + "</tr>").join("");
  c.innerHTML = `<table><thead><tr>${cab}</tr></thead><tbody>${filas}</tbody></table>`;
}
const colGuia = ["Guía", (p) => `<b>${esc(p.guia)}</b>`];
const colDest = ["Destinatario", (p) => esc(p.destinatario.nombre)];
const colCiudad = ["Destino", (p) => esc(p.destino.ciudad)];
const colEstado = ["Estado", chip];
const colPrecio = ["Precio", (p) => esc(dinero(p.tarifa))];
const seleccionados = (id) => [...document.querySelectorAll(`${id} .sel:checked`)].map((x) => x.value);
const porEstado = (...e) => paquetes.filter((p) => e.includes(p.estado));

/* ---------------------------------------------------------------- RASTREO */
let guiaActual = "";
$("#form-rastreo").addEventListener("submit", (e) => { e.preventDefault(); guiaActual = $("#guia-buscar").value.trim().toUpperCase(); rastrear(); });
async function rastrear() {
  const out = $("#resultado-rastreo");
  if (!guiaActual) { out.innerHTML = ""; return; }
  try {
    const p = await api("/paquetes/" + encodeURIComponent(guiaActual));
    const EXCEPCION = ["SEGUNDO_INTENTO_PENDIENTE", "RETENIDO_EN_SUCURSAL", "DIRECCION_INCORRECTA", "RETENIDO_POR_INCIDENCIA", "RECHAZADO_EN_DEVOLUCION"];
    const pos = EXCEPCION.includes(p.estado) ? FLUJO.indexOf("EN_REPARTO") : FLUJO.indexOf(p.estado);
    const pasos = FLUJO.map((s, i) => `<div class="${pos >= 0 && i < pos ? "done" : i === pos ? "now" : ""}">${NOMBRE_PASO[s]}</div>`).join("");
    const tono = clase(p.estado) || "info";
    const extra = p.requiere_autorizacion_tercer_intento ? `<div class="banner warn">Se necesita autorización de un supervisor para un tercer intento de entrega.</div>` : "";
    out.innerHTML = `<div class="card"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px"><h2>${esc(p.guia)}</h2>${chip(p)}</div>
      <div class="banner ${tono}">${esc(MENSAJE[p.estado] || "")}</div>${extra}
      <div class="steps">${pasos}</div>
      <div class="facts"><div><small>Para</small>${esc(p.destinatario.nombre)}</div><div><small>Destino</small>${esc(p.destino.calle)}, ${esc(p.destino.ciudad)}</div>
      <div><small>Servicio</small>${p.nivel_servicio === "EXPRES" ? "Exprés" : "Estándar"} · ${p.tarifa.dias_entrega} día(s)</div><div><small>Precio</small>${esc(dinero(p.tarifa))}</div>
      <div><small>Última actualización</small>${fecha(p.actualizado_en)}</div>${p.evidencia ? `<div><small>Recibió</small>${esc(p.evidencia.receptor)}</div>` : ""}</div>
      <h2 style="margin-top:18px">Recorrido</h2>
      <ul class="timeline">${[...p.linea_de_tiempo].reverse().map((t) => `<li><b>${esc(t.etiqueta)}</b> — ${esc(t.descripcion)}<small>${fecha(t.fecha)}${t.instalacion ? " · " + esc(t.instalacion) : ""}</small></li>`).join("")}</ul>
      ${p.incidencias.length ? `<h2>Incidencias</h2>` + p.incidencias.map((i) => `<div class="banner ${i.estado === "ABIERTA" ? "warn" : "ok"}">${esc(i.tipo.replace("_", " "))}: ${esc(i.estado === "ABIERTA" ? i.descripcion : i.resolucion)}</div>`).join("") : ""}</div>`;
  } catch (e) { out.innerHTML = `<div class="banner bad">${esc(e.message)}. Revisa que la guía esté bien escrita.</div>`; }
}
function verGuia(g) { guiaActual = g; $("#guia-buscar").value = g; ir("rastreo"); }

/* ---------------------------------------------------------------- SUCURSAL */
let cotizacionOk = false;
const camposEnvio = ["e-peso", "e-largo", "e-ancho", "e-alto", "e-ciudad", "e-nivel"];
camposEnvio.forEach((id) => $("#" + id).addEventListener("input", () => { cotizacionOk = false; $("#btn-registrar").disabled = true; $("#cotizacion").hidden = true; }));
const datosCotizacion = () => ({ peso_kg: $("#e-peso").value, largo_cm: $("#e-largo").value, ancho_cm: $("#e-ancho").value, alto_cm: $("#e-alto").value, destino_ciudad: $("#e-ciudad").value, nivel_servicio: $("#e-nivel").value });
$("#btn-cotizar").addEventListener("click", async () => {
  try {
    const t = await api("/cotizaciones", "POST", datosCotizacion());
    $("#cotizacion").hidden = false;
    $("#cotizacion").innerHTML = `<div class="price">${esc(t.texto)}</div>Entrega en ${t.dias_entrega} día(s) · zona ${esc(t.zona.toLowerCase())} · peso cobrado ${esc(t.peso_facturable_kg)} kg`;
    cotizacionOk = true; $("#btn-registrar").disabled = false;
  } catch (e) { aviso(e.message, "err"); }
});
$("#form-envio").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!cotizacionOk) return aviso("Primero calcula el precio", "err");
  const d = { ...datosCotizacion(), remitente_id: $("#e-remitente").value, destinatario_nombre: $("#e-dest").value, destinatario_telefono: $("#e-tel").value, destino_calle: $("#e-calle").value, contenido: $("#e-contenido").value, empleado: $("#e-empleado").value };
  const p = await intentar(() => api("/paquetes", "POST", d), "Paquete recibido");
  if (p) {
    $("#guia-generada").innerHTML = `<div class="guia-box"><div>Guía generada</div><div class="code">${esc(p.guia)}</div><div>${esc(dinero(p.tarifa))} · entrega estimada en ${p.tarifa.dias_entrega} día(s)</div></div>`;
    $("#form-envio").reset(); cotizacionOk = false; $("#btn-registrar").disabled = true; $("#cotizacion").hidden = true;
  }
});
async function pintarSucursal() {
  tabla("#lista-sucursal", paquetes.slice(0, 15), [colGuia, colDest, colEstado, colPrecio], {
    acciones: (p) => `<button data-ver="${esc(p.guia)}">Ver</button>` + (p.estado === "RECIBIDO" ? `<button class="danger" data-cancelar="${esc(p.guia)}">Cancelar</button>` : "")
      + (p.estado === "RECHAZADO_EN_DEVOLUCION" ? `<button data-devuelto="${esc(p.guia)}">Confirmar devolución</button>` : ""),
    vacio: "Todavía no hay envíos.",
  });
}
$("#lista-sucursal").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.dataset.ver) verGuia(b.dataset.ver);
  if (b.dataset.cancelar) intentar(() => api(`/paquetes/${b.dataset.cancelar}/cancelar`, "POST", { motivo: "Cancelado por el cliente" }), "Envío cancelado");
  if (b.dataset.devuelto) intentar(() => api(`/paquetes/${b.dataset.devuelto}/devolucion`, "POST", {}), "Devolución confirmada");
});

/* ---------------------------------------------------------------- CENTRO */
const infoLista = [colGuia, colDest, colCiudad, colEstado];
function pintarCentro() {
  tabla("#lista-clasificar", porEstado("RECIBIDO"), infoLista, { seleccion: true, vacio: "No hay paquetes por clasificar." });
  tabla("#lista-viaje", porEstado("CLASIFICADO"), infoLista, { seleccion: true, vacio: "No hay paquetes listos para viaje." });
  tabla("#lista-transito", porEstado("EN_TRANSITO"), infoLista, { seleccion: true, vacio: "No hay paquetes en tránsito." });
}
$("#btn-clasificar").addEventListener("click", async () => {
  const g = seleccionados("#lista-clasificar"); if (!g.length) return aviso("Marca al menos un paquete", "err");
  await intentar(async () => { for (const x of g) await api(`/paquetes/${x}/clasificar`, "POST", { instalacion: $("#c-inst1").value, operador: "Centro de distribución" }); }, "Paquetes clasificados");
});
$("#btn-despachar").addEventListener("click", async () => {
  const g = seleccionados("#lista-viaje"); if (!g.length) return aviso("Marca al menos un paquete", "err");
  await intentar(() => api("/manifiestos", "POST", { origen: $("#c-origen").value, destino: $("#c-destino").value, guias: g, operador: "Centro de distribución" }), "Viaje despachado: paquetes en tránsito");
});
$("#btn-llegada").addEventListener("click", async () => {
  const g = seleccionados("#lista-transito"); if (!g.length) return aviso("Marca al menos un paquete", "err");
  await intentar(async () => { for (const x of g) await api(`/paquetes/${x}/arribo`, "POST", { instalacion: $("#c-llegada").value, operador: "Centro destino" }); }, "Llegada registrada");
});

/* ---------------------------------------------------------------- REPARTO */
const nombreRep = () => $("#r-nombre").value.trim() || "Repartidor";
$("#r-nombre").value = localStorage.getItem("repartidor") || "";
$("#r-nombre").addEventListener("input", () => localStorage.setItem("repartidor", $("#r-nombre").value));
function pintarReparto() {
  tabla("#lista-cargar", porEstado("CENTRO_DESTINO", "SEGUNDO_INTENTO_PENDIENTE", "DIRECCION_INCORRECTA", "RETENIDO_POR_INCIDENCIA", "RETENIDO_EN_SUCURSAL"),
    [colGuia, colDest, ["Dirección", (p) => esc(p.destino.calle + ", " + p.destino.ciudad)], colEstado], { seleccion: true, vacio: "No hay paquetes por cargar." });
  tabla("#lista-reparto", porEstado("EN_REPARTO"), [colGuia, colDest, ["Dirección", (p) => esc(p.destino.calle + ", " + p.destino.ciudad)],
    ["Intentos", (p) => `${p.intentos_fallidos}` + (p.requiere_autorizacion_tercer_intento ? ' <span class="chip warn">pide autorización</span>' : "")]], {
    vacio: "No tienes paquetes en reparto.",
    acciones: (p) => `<button class="primary" data-a="entregar" data-g="${esc(p.guia)}">✅ Entregar</button><button data-a="ausente" data-g="${esc(p.guia)}">🚪 No estaba</button>`
      + `<button data-a="rechazo" data-g="${esc(p.guia)}">❌ Rechazó</button><button data-a="direccion" data-g="${esc(p.guia)}">📍 Dirección incorrecta</button><button data-a="dano" data-g="${esc(p.guia)}">⚠️ Dañado / perdido</button>`,
  });
}
$("#btn-ruta").addEventListener("click", async () => {
  const g = seleccionados("#lista-cargar"); if (!g.length) return aviso("Marca al menos un paquete", "err");
  await intentar(async () => {
    // Si venía de una pausa o reintento, reanudar; si no, iniciar ruta (centro destino)
    const nuevos = g.filter((x) => paquetes.find((p) => p.guia === x)?.estado === "CENTRO_DESTINO");
    for (const x of g.filter((y) => !nuevos.includes(y))) await api(`/paquetes/${x}/reanudar`, "POST", { repartidor: nombreRep() });
    if (nuevos.length) await api("/rutas", "POST", { repartidor: nombreRep(), guias: nuevos });
  }, "Ruta iniciada: tus paquetes están En reparto");
});
$("#lista-reparto").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  const g = b.dataset.g, accion = b.dataset.a;
  if (accion === "entregar") return dialogoEntrega(g);
  if (accion === "ausente") return intentar(() => api(`/paquetes/${g}/ausencia`, "POST", { repartidor: nombreRep() }), "Ausencia registrada");
  if (accion === "rechazo") return dialogoTexto("¿Por qué rechazó el paquete?", "Motivo", (v) => api(`/paquetes/${g}/rechazo`, "POST", { motivo: v, repartidor: nombreRep() }), "Rechazo registrado: el paquete regresa a origen");
  if (accion === "direccion") return dialogoTexto("¿Qué pasó con la dirección?", "Comentario (opcional)", (v) => api(`/paquetes/${g}/direccion-incorrecta`, "POST", { repartidor: nombreRep(), comentario: v }), "Entrega pausada y ticket enviado a Atención al cliente", false);
  if (accion === "dano") return dialogoIncidencia(g);
});

/* ---------------------------------------------------------------- diálogos */
const dlg = $("#dlg");
function abrir(html, alEnviar) {
  $("#dlg-body").innerHTML = html;
  const form = $("#dlg-form");
  form.onsubmit = async (ev) => { ev.preventDefault(); if ((await alEnviar()) !== false) { dlg.close(); refrescar(); } };
  $("#dlg-cancel")?.addEventListener("click", () => dlg.close());
  dlg.showModal();
}
const botones = (txt) => `<div class="dlg-actions"><button type="button" id="dlg-cancel">Cancelar</button><button class="primary">${txt}</button></div>`;
function dialogoTexto(titulo, etiqueta, enviar, ok, requerido = true) {
  abrir(`<h2>${esc(titulo)}</h2><label>${esc(etiqueta)}<input id="dlg-txt" ${requerido ? "required" : ""}></label>${botones("Confirmar")}`,
    async () => { const r = await intentar(() => enviar($("#dlg-txt").value), ok); return r !== undefined; });
}
function dialogoIncidencia(guia) {
  abrir(`<h2>Daño o pérdida</h2><p>No lo resuelvas en la calle: se avisará a Atención al cliente.</p>
    <label>Tipo<select id="dlg-tipo"><option value="DANO">Paquete dañado</option><option value="PERDIDA">Sospecha de pérdida</option></select></label>
    <label>Describe lo que viste<input id="dlg-txt" required></label>${botones("Reportar")}`,
    async () => { const r = await intentar(() => api(`/paquetes/${guia}/incidencia-mayor`, "POST", { tipo: $("#dlg-tipo").value, descripcion: $("#dlg-txt").value, repartidor: nombreRep() }), "Incidencia enviada a Atención al cliente"); return r !== undefined; });
}
function dialogoEntrega(guia) {
  abrir(`<h2>Confirmar entrega · ${esc(guia)}</h2>
    <label>Nombre de quien recibe<input id="dlg-rec" required></label>
    <p style="margin:10px 0 4px">Firma de quien recibe (dibuja con el dedo o mouse)</p><canvas id="firma" width="460" height="150"></canvas>
    <label style="margin-top:8px">o foto de recepción<input type="file" id="dlg-foto" accept="image/*" capture="environment"></label>
    <div class="banner info" style="font-size:14px">Sin firma o foto no se puede marcar como entregado.</div>
    <div class="dlg-actions"><button type="button" id="dlg-limpiar">Borrar firma</button><button type="button" id="dlg-cancel">Cancelar</button><button class="primary">Confirmar entrega</button></div>`,
    async () => {
      const lienzo = $("#firma"), archivo = $("#dlg-foto").files[0];
      const foto = archivo ? await leerArchivo(archivo) : null;
      const firma = lienzo.dataset.firmado ? lienzo.toDataURL("image/png") : null;
      const r = await intentar(() => api(`/paquetes/${guia}/entrega`, "POST", { receptor: $("#dlg-rec").value, firma, foto, repartidor: nombreRep() }), "¡Entrega registrada con evidencia!");
      return r !== undefined;
    });
  prepararFirma($("#firma"));
    $("#dlg-limpiar").onclick = () => { const l = $("#firma"); l.getContext("2d").clearRect(0, 0, l.width, l.height); l.trazo = 0; delete l.dataset.firmado; };
}
function leerArchivo(f) { return new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(f); }); }
function prepararFirma(c) {
  const x = c.getContext("2d"); x.lineWidth = 2.5; x.lineCap = "round"; x.strokeStyle = "#111";
  // Solo cuenta como firma un trazo real (>= 60 px dibujados); un clic o un punto suelto no basta.
  const MIN_TRAZO = 60;
  let dibujando = false, ultimo = null;
  c.trazo = 0;
  const pos = (e) => { const r = c.getBoundingClientRect(); return [(e.clientX - r.left) * c.width / r.width, (e.clientY - r.top) * c.height / r.height]; };
  c.onpointerdown = (e) => { dibujando = true; c.setPointerCapture(e.pointerId); ultimo = pos(e); x.beginPath(); x.moveTo(...ultimo); };
  c.onpointermove = (e) => {
    if (!dibujando) return;
    const p = pos(e);
    c.trazo += Math.hypot(p[0] - ultimo[0], p[1] - ultimo[1]);
    ultimo = p;
    x.lineTo(...p); x.stroke();
    if (c.trazo >= MIN_TRAZO) c.dataset.firmado = "1";
  };
  c.onpointerup = () => { dibujando = false; };
}

/* ---------------------------------------------------------------- ATENCION / SUPERVISOR */
function listaAutorizar(id, rol) {
  const lista = paquetes.filter((p) => p.requiere_autorizacion_tercer_intento && !p.tiene_evidencia && ["SEGUNDO_INTENTO_PENDIENTE", "EN_REPARTO"].includes(p.estado));
  tabla(id, lista, [colGuia, colDest, ["Intentos", (p) => p.intentos_fallidos], colEstado], {
    vacio: "Ningún paquete pide autorización.",
    acciones: (p) => `<button class="primary" data-aut="${esc(p.guia)}" data-rol="${rol}">Autorizar tercer intento</button>`,
  });
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-aut]"); if (!b) return;
  dialogoTexto("¿Quién autoriza?", "Tu nombre", (v) => api(`/paquetes/${b.dataset.aut}/autorizar-reintento`, "POST", { autorizador: v, rol: b.dataset.rol }), "Tercer intento autorizado");
});
async function pintarAtencion() {
  const inc = await api("/incidencias?estado=ABIERTA");
  const c = $("#lista-incidencias");
  if (!inc.length) c.innerHTML = '<div class="empty">No hay tickets abiertos.</div>';
  else c.innerHTML = `<table><thead><tr><th>Ticket</th><th>Guía</th><th>Tipo</th><th>Detalle</th><th></th></tr></thead><tbody>` + inc.map((i) =>
    `<tr><td>${esc(i.id)}</td><td><b>${esc(i.guia)}</b></td><td><span class="chip warn">${esc(i.tipo.replace("_", " "))}</span></td><td>${esc(i.descripcion)}</td><td class="btns"><button class="primary" data-res="${esc(i.id)}" data-tipo="${esc(i.tipo)}">Resolver</button><button data-ver="${esc(i.guia)}">Ver guía</button></td></tr>`).join("") + "</tbody></table>";
  listaAutorizar("#lista-autorizar-atn", "ATENCION_CLIENTE");
  pintarAvisos("#avisos-atn", "ATENCION_CLIENTE");
}
$("#lista-incidencias").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  if (!b.dataset.res) return;
  const dir = b.dataset.tipo === "DIRECCION_INCORRECTA";
  abrir(`<h2>Resolver ticket ${esc(b.dataset.res)}</h2><label>Tu nombre<input id="dlg-ag" required></label>
    <label>¿Cómo se resolvió?<input id="dlg-res" required></label>
    ${dir ? `<label>Calle y número corregidos<input id="dlg-calle" required></label><label>Ciudad<input id="dlg-ciu" required></label>` : ""}${botones("Resolver")}`,
    async () => { const r = await intentar(() => api(`/incidencias/${b.dataset.res}/resolver`, "POST", { agente: $("#dlg-ag").value, rol: "ATENCION_CLIENTE", resolucion: $("#dlg-res").value, nueva_calle: dir ? $("#dlg-calle").value : "", nueva_ciudad: dir ? $("#dlg-ciu").value : "" }), "Ticket resuelto"); return r !== undefined; });
});
async function pintarAvisos(id, destino) {
  const av = await api("/notificaciones?destino=" + destino);
  $(id).innerHTML = av.length ? av.slice(0, 8).map((a) => `<div class="banner info"><b>${esc(a.guia)}</b> · ${esc(a.mensaje)}<small style="display:block;color:var(--mute)">${fecha(a.creada_en)}</small></div>`).join("") : '<div class="empty">Sin avisos.</div>';
}
async function alertas(avisar) {
  try {
    const u = $("#s-umbral").value || 24;
    const lista = avisar ? await api("/alertas/ejecutar", "POST", { umbral_horas: u }) : await api("/alertas?umbral_horas=" + encodeURIComponent(u));
    tabla("#lista-alertas", lista, [["Guía", (a) => `<b>${esc(a.guia)}</b>`], ["Último estado", (a) => esc(a.ultimo_estado_etiqueta)], ["Horas sin cambios", (a) => a.horas_estancado], ["Última actualización", (a) => fecha(a.ultima_actualizacion)]], { vacio: "Sin paquetes estancados con ese umbral. 👍" });
    if (avisar) aviso(lista.length ? `${lista.length} alerta(s) enviadas al supervisor` : "Nada que avisar");
  } catch (e) { aviso(e.message, "err"); }
}
$("#btn-alertas").addEventListener("click", () => alertas(false));
$("#btn-avisar").addEventListener("click", async () => { await alertas(true); pintarAvisos("#avisos-sup", "SUPERVISOR"); });
document.addEventListener("click", (e) => { const b = e.target.closest("[data-ver]"); if (b && !b.closest("#lista-sucursal")) verGuia(b.dataset.ver); });

/* ---------------------------------------------------------------- AUDITORIA */
function pintarAuditoria() {
  tabla("#lista-entregados", porEstado("ENTREGADO"), [colGuia, colDest, ["Entregado", (p) => fecha(p.actualizado_en)]], {
    acciones: (p) => `<button data-evid="${esc(p.guia)}">Ver evidencia</button>`, vacio: "Aún no hay entregas concluidas.",
  });
}
$("#lista-entregados").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-evid]"); if (!b) return;
  try {
    const ev = await api(`/paquetes/${b.dataset.evid}/evidencia`);
    abrir(`<div class="evid"><h2>Evidencia · ${esc(ev.guia)}</h2><p>Recibió: <b>${esc(ev.receptor)}</b><br>${fecha(ev.capturada_en)}</p>
      ${ev.firma ? `<p>Firma</p><img alt="Firma" src="${esc(ev.firma)}">` : ""}${ev.foto ? `<p>Fotografía</p><img alt="Foto" src="${esc(ev.foto)}">` : ""}</div>
      <div class="dlg-actions"><button class="primary">Cerrar</button></div>`, async () => true);
  } catch (err) { aviso(err.message, "err"); }
});

/* ---------------------------------------------------------------- ciclo de refresco */
async function cargarCatalogos() {
  const rem = await api("/remitentes");
  $("#e-remitente").innerHTML = rem.filter((r) => r.activo).map((r) => `<option value="${esc(r.id)}">${esc(r.nombre)} (${esc(r.ciudad)})</option>`).join("");
  const opciones = INSTALACIONES.map((i) => `<option>${esc(i)}</option>`).join("");
  document.querySelectorAll("select.inst").forEach((s) => (s.innerHTML = opciones));
  $("#c-destino").selectedIndex = 2; $("#c-llegada").selectedIndex = 2;
}
async function refrescar() {
  if (document.querySelector("dialog[open]")) return; // no interrumpir un formulario abierto
  try {
    if (["sucursal", "centro", "reparto", "atencion", "supervisor", "auditoria"].includes(pestaña)) paquetes = await api("/paquetes");
    if (pestaña === "rastreo") await rastrear();
    if (pestaña === "sucursal") pintarSucursal();
    if (pestaña === "centro") pintarCentro();
    if (pestaña === "reparto") pintarReparto();
    if (pestaña === "atencion") await pintarAtencion();
    if (pestaña === "supervisor") { listaAutorizar("#lista-autorizar-sup", "SUPERVISOR"); pintarAvisos("#avisos-sup", "SUPERVISOR"); }
    if (pestaña === "auditoria") pintarAuditoria();
  } catch (e) { /* el servidor puede estar reiniciando; se reintenta en el siguiente ciclo */ }
}
cargarCatalogos().then(() => {
  const g = new URLSearchParams(location.search).get("guia");
  if (g) verGuia(g.toUpperCase());
  setInterval(refrescar, 6000);
});
