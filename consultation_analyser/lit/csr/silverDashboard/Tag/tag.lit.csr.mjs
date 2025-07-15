import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';


export default class Tag extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        status: { type: String },
        text: { type: String },
        subtext: { type: String },
        matchBackground: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-tag .tag {
                display: grid;
                width: max-content;
                max-width: 100%;
                gap: 0.5em; 
                padding: 0.3em 0.5em;
                font-size: 0.8em;
                line-height: 1.5em;
                color: white;
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
                align-items: center;
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
        this.matchBackground = false;
        
        this.applyStaticStyles("iai-silver-tag", Tag.styles);
    }

    getTagColor = (status) => {
        switch (status) {
            case this.CONSULTATION_STATUSES.open:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                    ternary: "var(--iai-silver-color-teal-mid)",
                };
            case this.CONSULTATION_STATUSES.analysing:
                return {
                    primary: "var(--iai-silver-color-pink)",
                    secondary: "var(--iai-silver-color-pink-light)",
                    ternary: "var(--iai-silver-color-pink-mid)",
                };
            case this.CONSULTATION_STATUSES.completed:
                return {
                    primary: "var(--iai-silver-color-teal)",
                    secondary: "var(--iai-silver-color-teal-light)",
                    ternary: "var(--iai-silver-color-teal-mid)",
                };
            case this.CONSULTATION_STATUSES.closed:
                return {
                    primary: "var(--iai-silver-color-amber)",
                    secondary: "var(--iai-silver-color-amber-light)",
                    ternary: "var(--iai-silver-color-amber-mid)",
                };
            default:
                return {
                    primary: "var(--iai-silver-color-dark)",
                    secondary: "var(--iai-silver-color-light)",
                    ternary: "var(--iai-silver-color-mid-light)",
                };
        }
    }

    render() {
        return html`
            <style>
                #${this.contentId} {
                    color: ${this.getTagColor(this.status).primary};
                    background: ${this.matchBackground
                        ? this.getTagColor(this.status).ternary
                        : this.getTagColor(this.status).secondary
                    };
                    border: 1px solid ${this.getTagColor(this.status).ternary};
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