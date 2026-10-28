import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import FileUpload from "./FileUpload.svelte";
import { CONSULTATION_ID } from "./mocks";

describe("FileUpload", () => {
  const TEST_DATA = {
    consultationId: CONSULTATION_ID,
  };

  it("matches snapshot", () => {
    const { container } = render(FileUpload, TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
