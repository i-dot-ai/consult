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
                background: var(--iai-silver-color-light);
                margin-bottom: 1em;
                font-size: 0.9em;
            }
            iai-tab-view .tab-button {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 0.5em;
                flex-grow: 1;
                padding: 0.5em;
                list-style: none;
                text-align: center;
                color: var(--iai-silver-color-dark);
                background: var(--iai-silver-color-light);
                border-radius: 0.5em;
                transition: 0.3s ease-in-out;
                cursor: pointer;
            }
            iai-tab-view .tab-button:hover {
                background: var(--iai-silver-color-mid-light);
            }
            iai-tab-view .tab-button.active {
                color: white;    
                background: var(--iai-silver-color-dark);
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
