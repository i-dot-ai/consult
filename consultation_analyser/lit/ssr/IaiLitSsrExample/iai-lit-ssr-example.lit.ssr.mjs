import { html, css } from "lit";
import IaiLitBase from "../../IaiLitBase.mjs";


export default class IaiLitSsrExample extends IaiLitBase {
    static styles = [
        IaiLitBase.styles,
        css`
            h2 {
                font-style: italic;
            }
        `
    ]

    static properties = {
        ...IaiLitBase.properties,
        // other properties
    }

    constructor() {
        super();
    }

    render() {
        const propsEntries = Object.entries(this.props);

        return html`
            <h1>Iai Lit Ssr Example Component</h1>
            ${propsEntries.length > 0
                ? html`
                    <h2>Props passed:</h2>
                    ${propsEntries.map(([key, value]) => html`
                        <ul>${key}: ${JSON.stringify(value)}</ul>
                    `)}
                `
                : html`<h2>No prop passed</h2>`
            }
        `
    }
}
customElements.define("iai-lit-ssr-example", IaiLitSsrExample)