import { describe, expect, it } from "vitest";

import { GET } from "./live";

describe("GET /live", () => {
  it("returns 200 regardless of any external state", async () => {
    const response = await GET({} as Parameters<typeof GET>[0]);

    expect(response.status).toBe(200);
  });

  it("returns JSON with status ok", async () => {
    const response = await GET({} as Parameters<typeof GET>[0]);
    const body = await response.json();

    expect(body.status).toBe("ok");
    expect(body.timestamp).toBeDefined();
  });
});
