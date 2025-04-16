import { expect, fixture, html } from '@open-wc/testing';
import "./iai-expanding-text.lit.csr.mjs";

describe('iai-expanding-text', () => {

  it('truncates text initially', async () => {
    const el = await fixture(html`
      <iai-expanding-text
        text="Test text"
        lines="10"
      ></iai-expanding-text>
    `);
    expect(el.querySelector(".iai-text-content").textContent.trim()).to.equal("Test text");
    expect(el.querySelector(".iai-text-content").classList.contains("iai-text-truncated")).to.be.true;
  });

  it('expands when clicked on', async () => {
    const el = await fixture(html`
      <iai-expanding-text
        text=${"Test text".repeat(50)}
        lines="1"
      ></iai-expanding-text>
    `);

    expect(el.querySelector(".iai-text-content").classList.contains("iai-text-truncated")).to.be.true;

    el.querySelector(".iai-text-content").click();
    await el.updateComplete;

    expect(el.querySelector(".iai-text-content").classList.contains("iai-text-truncated")).to.be.false;
  });

  it('always has full text in the markup', async () => {
    const el = await fixture(html`
      <iai-expanding-text
        text=${"Test text".repeat(50)}
        lines="1"
      ></iai-expanding-text>
    `);

    expect(el.querySelector(".iai-text-content").classList.contains("iai-text-truncated")).to.be.true;
    expect(el.querySelector(".iai-text-content").textContent.trim()).to.equal("Test text".repeat(50));

    el.querySelector(".iai-text-content").click();
    await el.updateComplete;

    expect(el.querySelector(".iai-text-content").classList.contains("iai-text-truncated")).to.be.false;
    expect(el.querySelector(".iai-text-content").textContent.trim()).to.equal("Test text".repeat(50));
  });

  it('focuses', async () => {
    const el = await fixture(html`
      <iai-expanding-text
        text="Test text"
        lines="1"
      ></iai-expanding-text>
    `);

    const expandingText = el.querySelector(".iai-text-content");

    document.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
    }))

    expandingText.focus();
    expect(document.activeElement).to.equal(expandingText);
  });
});