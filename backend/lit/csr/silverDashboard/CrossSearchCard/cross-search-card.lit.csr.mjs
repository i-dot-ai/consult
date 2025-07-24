import { html, css } from 'lit';

import SearchBox from '../inputs/SearchBox/search-box.lit.csr.mjs';
import SelectInput from '../inputs/SelectInput/select-input.lit.csr.mjs';
import Title from '../Title/title.lit.csr.mjs';
import Panel from '../Panel/panel.lit.csr.mjs';
import Card from '../Card/card.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import IaiIconButton from '../../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';
import Consultation from '../Consultation/consultation.lit.csr.mjs';

import IaiLitBase from '../../../IaiLitBase.mjs';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';


export default class CrossSearchCard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        aside: { type: String },
        description: { type: String },
        tags: { type: Array }, //  Array<String>
        type: { type: String }, //  "question" | "response"
        highlightText: { type: String },
        footer: { type: String },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-cross-search-card h3 {
                font-size: 0.9em;
                margin: 0;
            }
            iai-silver-cross-search-card .container {
                display: flex;
                gap: 0.5em;
            }
            iai-silver-cross-search-card .body-container {
                flex-grow: 1;
            }
            iai-silver-cross-search-card .title-container {
                display: flex;
                justify-content: space-between;
            }
            iai-silver-cross-search-card .tags {
                display: flex;
                gap: 0.5em;
                flex-wrap: wrap;
            }
            iai-silver-cross-search-card .tag {
                display: flex;
                justify-content: center;
                align-items: center;    
                padding: 0.3em 0.5em;
                background: #e6e6e7;
                font-size: 0.8em;
                border-radius: 0.5em;
            }
            iai-silver-cross-search-card .matched-text {
                background: yellow;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.aside = "";
        this.description = "";
        this.tags = [];
        this.type = "question";
        this.highlightText = "";
        this.footer = "";

        this.applyStaticStyles("iai-silver-cross-search-card", CrossSearchCard.styles);
    }

    applyTextHighlight = (text) => {
        if (!this.highlightText) {
            return text;
        }
        const regex = new RegExp(this.highlightText, "gi");
        return unsafeHTML(text.replace(regex, match => `<span class="matched-text">${match}</span>`));
    }

    render() {
        return html`
            <iai-silver-panel>
                <article slot="content">
                    <div class="container">
                        <div>
                            <iai-icon
                                .name=${this.type == "question" ? "help" : "chat_bubble"}
                                .color=${this.type == "question"
                                    ? "oklch(.6 .118 184.704)"
                                    : "oklch(.828 .189 84.429)"
                                }
                            ></iai-icon>
                        </div>

                        <div class="body-container">
                            <div class="title-container">
                                <h3>
                                    ${this.applyTextHighlight(this.title)}
                                </h3>

                                ${this.aside ? this.aside : ""}
                            </div>

                            <p>
                                ${this.applyTextHighlight(this.description)}
                            </p>

                            <footer class="tags">
                                ${this.footer}
                                ${this.tags.map(tag => html`
                                    <span class="tag">
                                        ${tag}
                                    </span>
                                `)}
                            </footer>
                        <div>
                    </div>
                </article>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-cross-search-card", CrossSearchCard);