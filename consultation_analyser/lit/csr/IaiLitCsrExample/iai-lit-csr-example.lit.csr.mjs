import { html, css } from 'lit';
import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiLitCsrExample extends IaiLitBase {
    static styles = [
        IaiLitBase.styles,
        css`
            span {
                color: salmon;
            }
        `
    ]

    constructor() {
        super();
    }
    render() {
        return html`<p>Iai Lit <span>Csr</span> Component</p>`
    }
}
customElements.define("iai-lit-csr-example", IaiLitCsrExample)