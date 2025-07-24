import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';


export default class Button extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        text: { type: String },
        handleClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-button button {
                background: white;
                outline: none;
                border: 1px solid var(--iai-silver-color-mid-light);
                padding: 0.5em 1em;
                border-radius: 0.5em;
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-silver-button button:hover {
                background: var(--iai-silver-color-light);
            }
            iai-silver-button button:focus-visible {
                outline: 3px solid #fd0;
                outline-offset: 0;
                box-shadow: inset 0 0 0 2px;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.text = "white";
        this.handleClick = () => {};

        this.applyStaticStyles("iai-silver-button", Button.styles);
    }

    render() {
        return html`
            <button @click=${this.handleClick}>
                ${this.text}
            </button>
        `
    }
}
customElements.define("iai-silver-button", Button);