import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class IaiIcon extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        name: { type: String },
        color: { type: String },
        fill: {type: Number }, //  0 | 1
        opsz: { type: Number },
        wght: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-icon {
                display: flex;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Google expect icon names to be alphabetically sorted
        this._ALL_ICON_NAMES = ["visibility", "close", "star", "search", "thumb_up", "thumb_down", "thumbs_up_down", "arrow_drop_down_circle", "download", "diamond", "progress_activity", "sort", "schedule", "calendar_month", "group", "description", "monitoring", "settings", "help", "chat_bubble", "wand_stars", "lan", "finance", "filter_alt", "network_intelligence", "arrow_downward", "arrow_upward", "report", "chevron_left", "keyboard_arrow_down"];
        this._URL = "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=" + [...this._ALL_ICON_NAMES].sort().join(",");

        // Prop defaults
        this.name = "";
        this.color = "";
        this.fill = 0;
        this.opsz = 48;
        this.wght = 300;
        
        this.applyStaticStyles("iai-icon", IaiIcon.styles);
    }

    firstUpdated() {
        this.addIconImport();
    }

    addIconImport() {
        // Do not add if already added
        if (document.querySelector(`link[href="${this._URL}"]`)) {
            return;
        }

        const linkElement = document.createElement("link");
        linkElement.rel = "stylesheet";
        linkElement.href = this._URL;
        document.head.append(linkElement);
    }

    render() {
        return html`
            <style>
                #${this.contentId}.material-symbols-outlined {
                    font-variation-settings:
                        'FILL' ${this.fill},
                        'opsz' ${this.opsz},
                        'wght' ${this.wght};
                    color: ${this.color};
                }
            </style>
            <span id=${this.contentId} class="material-symbols-outlined">
                ${this.name}
            </span>
        `;
    }
}
customElements.define("iai-icon", IaiIcon);