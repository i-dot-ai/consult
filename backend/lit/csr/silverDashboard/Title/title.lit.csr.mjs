import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IconTile from '../IconTile/icon-tile.lit.csr.mjs';


export default class Title extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        level: { type: Number },
        text: { type: String },
        subtext: { type: String },
        icon: { type: String },
        aside: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-title h1,
            iai-silver-title h2,
            iai-silver-title h3,
            iai-silver-title h4 {
                margin: 0;
            }
            iai-silver-title h1 {
                font-size: 1.3em;
            }
            iai-silver-title h2 {
                font-size: 1em;
            }
            iai-silver-title h3,
            iai-silver-title h4 {
                font-size: 0.9em;
            }
            iai-silver-title .container {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }
            iai-silver-title .icon-container {
                display: flex;
                align-items: center;
                gap: 0.5em;
                margin-bottom: 1.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.level = 2;
        this.text = "";
        this.subtext = "";
        this.icon = "";
        this.aside = "";

        this.applyStaticStyles("iai-silver-title", Title.styles);
    }

    renderTitleTag = () => {
        switch (this.level) {
            case 1:
                return html`<h1>${this.text}</h1>`;
            case 2:
                return html`<h2>${this.text}</h2>`;
            case 3:
                return html`<h3>${this.text}</h3>`;
            case 4:
                return html`<h4>${this.text}</h4>`;
        }
    }

    render() {
        return html`
        <div class="container">
            <div class="icon-container">
                ${this.icon
                    ? html`
                        <iai-silver-icon-tile
                            .backgroundColor=${"var(--iai-silver-color-accent-light)"}
                            .color=${"var(--iai-silver-color-accent)"}
                            .name=${this.icon}
                        ></iai-silver-icon-tile>
                    `
                    : ""
                }

                <div>
                    ${this.renderTitleTag()}

                    ${this.subtext
                        ? html`
                            <small>
                                ${this.subtext}
                            </small>
                        `
                        : ""
                    }
                </div>
            </div>

            <aside>
                ${this.aside}
            </aside>
        </div>
        `
    }
}
customElements.define("iai-silver-title", Title);