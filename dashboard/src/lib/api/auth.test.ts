import { describe, it, expect, beforeEach } from "vitest";
import {
  clearTokens,
  getStoredRefreshToken,
  getStoredToken,
  storeTokens,
  authHeaders,
} from "./auth";

describe("auth token storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("stores and retrieves tokens", () => {
    storeTokens("access-abc", "refresh-xyz");
    expect(getStoredToken()).toBe("access-abc");
    expect(getStoredRefreshToken()).toBe("refresh-xyz");
  });

  it("clears tokens", () => {
    storeTokens("a", "r");
    clearTokens();
    expect(getStoredToken()).toBeNull();
    expect(getStoredRefreshToken()).toBeNull();
  });

  it("builds auth headers when token present", () => {
    storeTokens("tok", "ref");
    expect(authHeaders()).toEqual({
      Authorization: "Bearer tok",
    });
  });

  it("returns empty headers when no token", () => {
    expect(authHeaders()).toEqual({});
  });
});
