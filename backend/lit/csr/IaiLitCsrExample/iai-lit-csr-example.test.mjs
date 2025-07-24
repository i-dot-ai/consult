import { expect, fixture, html } from '@open-wc/testing';
import "./iai-lit-csr-example.lit.csr.mjs";

describe('iai-lit-csr-example', () => {
  it('renders text correctly', async () => {
    const el = await fixture(html` <iai-lit-csr-example></iai-lit-csr-example> `);
    expect(el.textContent).to.equal("Iai Lit Csr Component");
    expect(el.outerHTML).to.include("<span>Csr</span>");
  });

  it('does not render to shadow DOM by default', async () => {
    const el = await fixture(html` <iai-lit-csr-example></iai-lit-csr-example> `);
    expect(el.outerHTML).to.not.include("template");
  });
});