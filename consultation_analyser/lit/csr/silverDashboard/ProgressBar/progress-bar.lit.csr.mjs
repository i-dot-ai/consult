

import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiProgressBar from '../../IaiProgressBar/iai-progress-bar.lit.csr.mjs';


export default class ProgressBar extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        value: { type: Number },
        variant: { type: String }, //  "primary" | "secondary"
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-progress-bar {
                flex-grow: 1;
            }
            iai-silver-progress-bar iai-progress-bar .container {
                border-radius: 0.5em;
                background: var(--iai-silver-color-mid);
                border: none;
                opacity: 0.7;
            }
            iai-silver-progress-bar .bar {
                height: 0.5em;
                border-top-left-radius: 0.5em;
                border-bottom-left-radius: 0.5em;
                background: var(--iai-silver-color-dark);
            }
            iai-silver-progress-bar iai-progress-bar.primary .bar {
                background: var(--iai-silver-color-accent);
            }
            iai-silver-progress-bar iai-progress-bar.primary .container {
                background: var(--iai-silver-color-mid-light);
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        this.value = 0;
        this.variant = "primary";
        
        this.applyStaticStyles("iai-silver-progress-bar", ProgressBar.styles);
    }

    render() {
        return html`
            <iai-progress-bar
                class=${this.variant === "primary" ? "primary" : "secondary"}
                .value=${this.value}
                .label=${""}
            ></iai-progress-bar>
        `;
    }
}
customElements.define("iai-silver-progress-bar", ProgressBar);
