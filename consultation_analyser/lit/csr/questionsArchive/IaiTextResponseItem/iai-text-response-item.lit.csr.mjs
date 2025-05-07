import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiTextResponseItem extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        iconName: { type: String },
        text: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-text-response-item p {
                margin: 0;
            }
            iai-text-response-item li {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 1em;
            }
            iai-text-response-item li {
                margin-bottom: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.iconName = "";
        this.text = "";

        this.applyStaticStyles("iai-text-response-item", IaiTextResponseItem.styles);
    }

    render() {
        return html`
            <li>
                <iai-icon
                    name="${this.iconName}"
                    .color=${"var(--iai-colour-text-secondary)"}
                    .fill=${0}
                ></iai-icon>
                <p>
                    ${this.text}
                </p>
            </li>
        `;
    }
}
customElements.define("iai-text-response-item", IaiTextResponseItem);