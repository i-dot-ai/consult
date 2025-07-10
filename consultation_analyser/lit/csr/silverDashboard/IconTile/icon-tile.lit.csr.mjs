import { html, css } from 'lit';

import IaiIcon from '../../IaiIcon/iai-icon.mjs';

import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IconTile extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        color: { type: String },
        backgroundColor: { type: String },
        name: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-icon-tile {
                display: block;    
                width: max-content;
            }
            iai-silver-icon-tile .icon-tile-container {
                display: flex;    
                justify-content: center;
                align-items: center;
                background: salmon;
                padding: 0.4em;
                border-radius: 0.5em;
            }
            iai-silver-icon-tile .material-symbols-outlined {
                font-size: 2em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.color = "white";
        this.backgroundColor = "black";
        this.name = "";

        this.applyStaticStyles("iai-silver-icon-tile", IconTile.styles);
    }

    render() {
        return html`
            <style>
                #${this.contentId} {
                    color: ${this.color};
                    background: ${this.backgroundColor};
                }
            </style>
            <div id=${this.contentId} class="icon-tile-container">
                <iai-icon
                    .name=${this.name}
                ></iai-icon>
            </div>
        `
    }
}
customElements.define("iai-silver-icon-tile", IconTile);