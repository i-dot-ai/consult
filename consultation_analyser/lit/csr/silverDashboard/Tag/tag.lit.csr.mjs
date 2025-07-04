import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';


export default class Tag extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        status: { type: String },
        text: { type: String },
        subtext: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-tag .tag {
                display: grid;
                width: max-content;
                gap: 0.5em; 
                padding: 0.3em 0.5em;
                font-size: 0.8em;
                color: white;
                background: #85d07e;                
                border-radius: 0.5em;
            }
            iai-silver-tag iai-icon {
                margin-right: 0.3em;
            }
            iai-silver-tag iai-icon .material-symbols-outlined {
                font-size: 1.3em;
            }
            iai-silver-tag .text-container {
                display: flex;
                font-weight: bold;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.status = "";
        this.text = "";
        this.subtext = "";
        
        this.applyStaticStyles("iai-silver-tag", Tag.styles);
    }

    getTagColor = (status) => {
        switch (status) {
            case this.CONSULTATION_STATUSES.open:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.analysing:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.completed:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                };
            case this.CONSULTATION_STATUSES.closed:
                return {
                    primary: "var(--iai-silver-color-amber)",
                    secondary: "var(--iai-silver-color-amber-light)",
                };
        }
    }

    render() {
        return html`
            <style>
                #${this.contentId} {
                    color: ${this.getTagColor(this.status).primary};
                    background: ${this.getTagColor(this.status).secondary};
                    border: 1px solid ${this.getTagColor(this.status).primary};
                }
            </style>
            
            <span id=${this.contentId} class="tag">
                <span class="text-container">
                    ${this.icon
                        ? html`
                            <iai-icon
                                .name=${this.icon}
                                .color=${this.getTagColor(this.status).primary}
                            ></iai-icon>
                        `
                        : ""
                    }
                    ${this.text}
                </span>

                ${this.subtext ? html`
                    <span>
                        ${this.subtext}
                    </span>    
                ` : ""}
            </span>
        `
    }
}
customElements.define("iai-silver-tag", Tag);