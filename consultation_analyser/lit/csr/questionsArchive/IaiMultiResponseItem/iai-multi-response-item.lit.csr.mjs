import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiProgressBar from '../../IaiProgressBar/iai-progress-bar.lit.csr.mjs';


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
            iai-multi-response-item iai-progress-bar .container .bar {
                height: 1.3em;
            }
            iai-multi-response-item iai-progress-bar .container .label,
            iai-multi-response-item iai-progress-bar .container.low-value .label {
                font-size: 0.9em;
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

    getPercentage = (part, whole) => {
        if (part === 0){
            return 0;
        }
        return Math.round((part / whole) * 100);
    }

    render() {
        return html`
            <li>
                <p>
                    ${this.countName ? this.countName + ": " : ""}<strong>${this.countValue}</strong>
                </p>
                <iai-progress-bar
                    .value=${this.getPercentage(this.countValue, this.totalCounts)}
                    .label=${this.getPercentage(this.countValue, this.totalCounts) + "%"}
                ></iai-progress-bar>
            </li>
        `;
    }
}
customElements.define("iai-multi-response-item", IaiMultiResponseItem);