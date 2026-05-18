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

    async init() {
      await this.hidratarTokens();
      await this.recarregar();
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
      if (s === "running") return "rodando";
      if (s === "ok") return "ok";
      if (s === "warn") return "aviso";
      if (s === "fail") return "falha";
      return "sem teste";
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
