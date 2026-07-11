import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 20 },
    { duration: "1m", target: 50 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

const BASE = __ENV.VOXERA_BASE_URL || "http://localhost:8000";

export default function () {
  const live = http.get(`${BASE}/api/v1/health/live`);
  check(live, { "live 200": (r) => r.status === 200 });

  const ready = http.get(`${BASE}/api/v1/health/ready`);
  check(ready, { "ready ok": (r) => r.status === 200 || r.status === 503 });

  const metrics = http.get(`${BASE}/api/v1/metrics`);
  check(metrics, { "metrics 200": (r) => r.status === 200 });

  sleep(1);
}
