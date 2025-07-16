import { html, css } from 'lit';

import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import IaiLitBase from '../../IaiLitBase.mjs';


export default class TabView extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        tabs: { type: Array },
        activeTab: { type: String },
        handleTabChange: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-tab-view nav {
                display: flex;
                max-width: max-content;
                margin: auto;
                margin-bottom: 1em;
                border-radius: 10em;
                font-size: 0.9em;
                background: var(--iai-silver-color-mid-light);
            }
            iai-tab-view .tab-button {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 0.5em;
                margin: 0.3em;
                padding: 0.5em;
                border-radius: 10em;
                list-style: none;
                text-align: center;
                font-size: 0.9em;
                color: var(--iai-silver-color-dark);
                transition: 0.3s ease-in-out;
                cursor: pointer;
            }
            iai-tab-view .tab-button:hover {
                background: var(--iai-silver-color-light);
            }
            iai-tab-view .tab-button.active {
                color: var(--iai-silver-color-dark);
                background: white;
            }
            iai-tab-view .tab-button .material-symbols-outlined {
                font-size: 1.3em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        console.log(this.tabs)
        this.tabs = [];
        this.activeTab = 0;
        this.handleTabChange = () => {};

        this.applyStaticStyles("iai-tab-view", TabView.styles);
    }

    render() {
        return html`
            <nav>
                ${this.tabs.map((tab, index) => html`
                    <li
                        role="button"
                        tabindex="0"
                        class=${"tab-button" + (this.activeTab === index ? " active" : "")}
                        @click=${() => this.handleTabChange(index)}
                    >
                        ${tab.title}
                    </li>
                `)}
            </nav>
            <div>
                ${this.tabs.map((tab, index) => html`
                    <section class=${this.activeTab === index ? "" : "visually-hidden"}>
                        ${tab.content}
                    </section>
                `)}
            </div>
        `;
    }
}
customElements.define("iai-tab-view", TabView);
