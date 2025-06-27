import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';


export default class Panel extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        borderColor: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-panel .panel {
                padding: 1em;
                border: 1px solid;
                border-radius: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        // Prop defaults
        this.borderColor = "";

        this.applyStaticStyles("iai-silver-panel", Panel.styles);
    }

    updated() {
        this.applySlots("content");
    }

    render() {
        return html`
            <style>
                #${this.contentId} {
                    border-color: ${this.borderColor || "var(--iai-silver-color-mid-light)"};
                }
            </style>
            <div id=${this.contentId} class="panel">
                <slot name="content"></slot>
            </div>
        `
    }
}
customElements.define("iai-silver-panel", Panel);