// Nyx Cockpit -- Alpine.js state + HTMX bindings (COCKPIT-03).
// Hidrata CSS vars via /api/tokens. Lista features de /api/features.
// Dispara gauntlet single via POST /api/features/{id}/run + poll status.

function dashboard() {
  return {
    features: [],
    categorias: [],
    counters: { ok: 0, warn: 0, fail: 0, unknown: 0, running: 0 },
    filtro: { categoria: "", status: "" },
    running: {},   // {feature_id: job_id}
    output: {},    // {feature_id: tail do output}
    pollers: {},   // {feature_id: timeout handle}
    // UX-COCKPIT-EXPERIENCE-01: microcopy hidratado de /api/microcopy
    copy: {
      running: "rodando", ok: "ok", warn: "aviso", fail: "falha",
      unknown: "sem teste", run_gauntlet: "rodar gauntlet",
      cancel: "cancelar", cancelled: "cancelado", reload: "recarregar",
      category: "categoria", status: "status", all: "todos", all_f: "todas",
      tooltip_run: "", tooltip_filter_cat: "", tooltip_filter_status: "",
      footer: "ADR-001 Local First | bind 127.0.0.1 | paleta D",
    },

    async init() {
      await Promise.all([this.hidratarTokens(), this.hidratarMicrocopy()]);
      await this.recarregar();
    },

    async hidratarMicrocopy() {
      try {
        const r = await fetch("/api/microcopy");
        if (!r.ok) return;
        const data = await r.json();
        Object.assign(this.copy, data.strings || {});
      } catch (e) { console.warn("hidratarMicrocopy falhou:", e); }
    },

    async hidratarTokens() {
      try {
        const r = await fetch("/api/tokens");
        if (!r.ok) return;
        const t = await r.json();
        const root = document.documentElement;
        const map = {
          "--nyx-accent":     t.accent,
          "--nyx-accent-dim": t.accent_dim,
          "--nyx-purple":     t.purple,
          "--nyx-purple-dim": t.purple_dim,
          "--nyx-primary":    t.primary,
          "--nyx-muted":      t.muted,
          "--nyx-bg":         t.bg,
          "--nyx-bg-soft":    t.bg_soft,
          "--nyx-success":    t.success,
          "--nyx-warning":    t.warning,
          "--nyx-error":      t.error,
        };
        for (const k in map) if (map[k]) root.style.setProperty(k, map[k]);
      } catch (e) { console.warn("hidratarTokens falhou:", e); }
    },

    async recarregar() {
      try {
        const r = await fetch("/api/features");
        const data = await r.json();
        this.features = data.features || [];
        this.categorias = [...new Set(this.features.map(f => f.categoria).filter(Boolean))].sort();
        this.recomputarCounters();
      } catch (e) {
        console.error("recarregar features falhou:", e);
      }
    },

    recomputarCounters() {
      const c = { ok: 0, warn: 0, fail: 0, unknown: 0, running: 0 };
      for (const f of this.features) {
        const s = this.statusOf(f);
        if (c[s] !== undefined) c[s]++;
      }
      this.counters = c;
    },

    statusOf(f) {
      if (this.running[f.id]) return "running";
      const s = (f.status || "").toLowerCase();
      if (s === "ok" || s === "verde" || s === "ok-passou") return "ok";
      if (s === "aviso" || s === "amarelo" || s === "warn") return "warn";
      if (s === "fail" || s === "vermelho" || s === "falhou") return "fail";
      return "unknown";
    },

    statusLabel(f) {
      const s = this.statusOf(f);
      return this.copy[s] || s;
    },

    async cancelar(featureId) {
      // UX-COCKPIT-EXPERIENCE-01 (ADR-026): cancel nomeado.
      // Front cancela apenas o poll local; gauntlet subprocess no servidor
      // continua até timeout. Anti-debito COCKPIT-04-CANCEL-RUN-01 (futuro)
      // adicionaria DELETE /api/features/{id}/run para cancelar de fato.
      if (this.pollers[featureId]) {
        clearTimeout(this.pollers[featureId]);
        delete this.pollers[featureId];
      }
      delete this.running[featureId];
      this.output[featureId] = "[" + this.copy.cancelled + "] (subprocess pode continuar ate timeout)";
      this.recomputarCounters();
    },

    get filtered() {
      return this.features.filter(f => {
        if (this.filtro.categoria && f.categoria !== this.filtro.categoria) return false;
        if (this.filtro.status && this.statusOf(f) !== this.filtro.status) return false;
        return true;
      });
    },

    async rodar(featureId) {
      if (this.running[featureId]) return;
      this.output[featureId] = "iniciando gauntlet...";
      try {
        const r = await fetch(`/api/features/${featureId}/run`, { method: "POST" });
        if (!r.ok) {
          this.output[featureId] = `[erro] ${r.status} ${r.statusText}`;
          return;
        }
        const data = await r.json();
        this.running[featureId] = data.job_id;
        this.recomputarCounters();
        this.poll(featureId, data.job_id);
      } catch (e) {
        this.output[featureId] = "[erro] " + e.message;
      }
    },

    poll(featureId, jobId) {
      const tick = async () => {
        try {
          const r = await fetch(`/api/features/${featureId}/status/${jobId}`);
          if (!r.ok) {
            this.output[featureId] = `[poll erro] ${r.status}`;
            delete this.running[featureId];
            this.recomputarCounters();
            return;
          }
          const data = await r.json();
          this.output[featureId] = `[${data.status}] ${data.duration.toFixed(1)}s\n${data.output_tail || ""}`;
          if (data.status === "running") {
            this.pollers[featureId] = setTimeout(tick, 1500);
          } else {
            delete this.running[featureId];
            // Atualiza status no objeto local (poderia recarregar tudo, mas
            // mantém UX fluida com update minimal).
            const f = this.features.find(x => x.id === featureId);
            if (f) {
              if (data.status === "ok") f.status = "ok";
              else if (data.status === "fail") f.status = "fail";
              else if (data.status === "timeout") f.status = "fail";
              else if (data.status === "error") f.status = "fail";
            }
            this.recomputarCounters();
          }
        } catch (e) {
          this.output[featureId] = "[poll erro] " + e.message;
          delete this.running[featureId];
          this.recomputarCounters();
        }
      };
      tick();
    },
  };
}
