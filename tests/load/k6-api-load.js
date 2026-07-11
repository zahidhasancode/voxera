import http from "k6/http";
import { check, sleep } from "k6";

/**
 * API load profile — 5000 requests over staged concurrency.
 * Run: k6 run tests/load/k6-api-load.js -e VOXERA_BASE_URL=http://localhost:8000
 */
export const options = {
  scenarios: {
    api_ramp: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 50 },
        { duration: "2m", target: 100 },
        { duration: "1m", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<800", "p(99)<1500"],
  },
};

const BASE = __ENV.VOXERA_BASE_URL || "http://localhost:8000";

export default function () {
  const endpoints = [
    "/api/v1/health/live",
    "/api/v1/health/ready",
    "/api/v1/metrics",
  ];
  const path = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(`${BASE}${path}`);
  check(res, {
    "status acceptable": (r) => r.status >= 200 && r.status < 500,
  });
  sleep(0.2);
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify(
      {
        suite: "api-load",
        requests: data.metrics.http_reqs?.values?.count ?? 0,
        p95_ms: data.metrics.http_req_duration?.values?.["p(95)"] ?? null,
        failed_rate: data.metrics.http_req_failed?.values?.rate ?? null,
      },
      null,
      2,
    ),
  };
}
