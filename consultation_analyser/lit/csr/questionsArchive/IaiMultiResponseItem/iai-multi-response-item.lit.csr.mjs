import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiMultiResponseItem extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        countName: { type: String },
        countValue: { type: Number },
        totalCounts: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-multi-response-item p {
                margin: 0;
            }
            iai-multi-response-item progress {
                width: 100%;
            }
            iai-multi-response-item progress {
                accent-color: var(--iai-colour-pink);
            }
            iai-multi-response-item li {
                margin-bottom: 0.5em;
                list-style: none;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.key = "";
        this.count = 0;
        this.totalCounts = 0;

        this.applyStaticStyles("iai-multi-response-item", IaiMultiResponseItem.styles);
    }

    render() {
        return html`
            <li>
                <p>
                    ${this.countName ? this.countName + ": " : ""}<strong>${this.countValue}</strong>
                </p>
                <progress value=${this.countValue} max=${this.totalCounts}></progress>
            </li>
        `;
    }
}
customElements.define("iai-multi-response-item", IaiMultiResponseItem);