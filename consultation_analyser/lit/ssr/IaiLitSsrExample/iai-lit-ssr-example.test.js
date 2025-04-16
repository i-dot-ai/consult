const { join } = require("path");

const { renderLitSsr } = require("../../testUtils");


describe('iai-lit-ssr-example', () => {
  const componentPath = join(__dirname, "iai-lit-ssr-example.lit.ssr.mjs");

  it('rendered props correctly', async () => {
    const result = renderLitSsr(componentPath, {"foo": ["bar", "baz"]});
    expect(result).toContain("Props passed:");
    expect(result).toContain("foo");
    expect(result).toContain("bar");
    expect(result).toContain("baz");
  });

  it('does not render to shadow DOM by default', async () => {
    const result = renderLitSsr(componentPath, {"foo": ["bar", "baz"]});
    expect(result).not.toContain("template");
  });

  it('renders correct text if no props are passed', async () => {
    const result = renderLitSsr(componentPath);
    expect(result).toContain("No prop passed");
  });
});