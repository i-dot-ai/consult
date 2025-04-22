import { expect, fixture, html } from '@open-wc/testing';
import "./iai-text-with-fallback.lit.csr.mjs";

describe('iai-text-with-fallback', () => {
  it('renders text if condition not met', async () => {
    const text = "Test Text"
    const fallbackText = "Fallback Text"

    const el = await fixture(html`
      <iai-text-with-fallback
        text=${text}
        fallback=${fallbackText}
      ></iai-text-with-fallback>
    `);
    expect(el.textContent.trim()).to.equal(text);
    expect(el.textContent.trim()).to.not.include(fallbackText);
  });

  it('renders fallback text if default condition of falsy text is met', async () => {
    const text = ""
    const fallbackText = "Fallback Text"

    const el = await fixture(html`
      <iai-text-with-fallback
        text=${text}
        fallback=${fallbackText}
      ></iai-text-with-fallback>
    `);
    expect(el.textContent.trim()).to.equal(fallbackText);
  });

  it('renders fallback text based on custom condition function', async () => {
    const text = "Test Text 01";
    const fallbackText = "Text cannot include digits";

    const el = await fixture(html`
      <iai-text-with-fallback
        text=${text}
        fallback=${fallbackText}
        .fallbackCondition=${(text) => /\d/.test(text)}
      ></iai-text-with-fallback>
    `);
    expect(el.textContent.trim()).to.equal(fallbackText);
  });

  it('renders fallback class if fallback is displayed', async () => {
    const text = ""
    const fallbackText = "Fallback Text"

    const el = await fixture(html`
      <iai-text-with-fallback
        text=${text}
        fallback=${fallbackText}
      ></iai-text-with-fallback>
    `);
    expect(el.outerHTML).to.include("fallback-active");
  });

  it('does not render fallback class if fallback is not displayed', async () => {
    const text = "Test Text"
    const fallbackText = "Fallback Text"

    const el = await fixture(html`
      <iai-text-with-fallback
        text=${text}
        fallback=${fallbackText}
      ></iai-text-with-fallback>
    `);
    expect(el.outerHTML).to.not.include("fallback-active");
  });
});