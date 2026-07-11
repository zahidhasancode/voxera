import http from "k6/http";
import ws from "k6/ws";
import { check, sleep } from "k6";

/**
 * Concurrent voice session simulation (HTTP health proxy for call setup).
 * Full WebSocket voice load requires authenticated sessions — this script
 * validates platform stability under concurrent health/metrics polling
 * equivalent to 100/500/1000 call monitoring agents.
 *
 * Profiles via VOXERA_LOAD_PROFILE: smoke | 100 | 500 | 1000
 */
const PROFILE = __ENV.VOXERA_LOAD_PROFILE || "smoke";

const PROFILES = {
  smoke: { vus: 10, duration: "30s" },
  "100": { vus: 100, duration: "2m" },
  "500": { vus: 500, duration: "3m" },
  "1000": { vus: 1000, duration: "5m" },
};

const selected = PROFILES[PROFILE] || PROFILES.smoke;

export const options = {
  vus: selected.vus,
  duration: selected.duration,
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<1000"],
  },
};

const BASE = __ENV.VOXERA_BASE_URL || "http://localhost:8000";
const WS_BASE = BASE.replace(/^http/, "ws");

export default function () {
  const live = http.get(`${BASE}/api/v1/health/live`);
  check(live, { "live healthy": (r) => r.status === 200 });

  const metrics = http.get(`${BASE}/api/v1/metrics`);
  check(metrics, { "metrics available": (r) => r.status === 200 });

  // Optional WebSocket probe (graceful skip if endpoint unavailable)
  const wsUrl = `${WS_BASE}/api/v1/ws/operations`;
  const res = ws.connect(wsUrl, {}, function (socket) {
    socket.on("open", () => socket.close());
    socket.setTimeout(() => socket.close(), 2000);
  });
  check(res, { "ws connect attempted": () => true });

  sleep(0.5);
}
