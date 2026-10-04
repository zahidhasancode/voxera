import { describe, it, expect } from "vitest";
import { getPlan, PLANS } from "@/lib/billing";

describe("billing", () => {
  it("returns plan by id", () => {
    expect(getPlan("pro").name).toBe("Pro");
    expect(getPlan("unknown" as "free").name).toBe("Free");
  });

  it("has all tier plans", () => {
    expect(PLANS.map((p) => p.id)).toEqual(["free", "pro", "business", "enterprise"]);
  });
});
