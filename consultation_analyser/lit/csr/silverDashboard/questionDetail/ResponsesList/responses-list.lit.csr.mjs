import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Panel from '../../Panel/panel.lit.csr.mjs';
import Tag from '../../Tag/tag.lit.csr.mjs';
import IaiVirtualList from '../../../IaiVirtualList/iai-virtual-list.lit.csr.mjs';
import IaiLoadingIndicator from '../../../IaiLoadingIndicator/iai-loading-indicator.lit.csr.mjs';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
import Button from '../../Button/button.lit.csr.mjs';


export default class ResponsesList extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        responses: { type: Array },
        responsesTotal: { type: Number },
        filteredTotal: { type: Number },
        handleScrollEnd: { type: Function },
        isLoading: { type: Boolean },
        highlightedText: { type: String },
        handleThemeTagClick: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-responses-list ul {
                padding-left: 0;
            }
            iai-silver-responses-list li {
                list-style: none;
            }
            iai-silver-responses-list article {
                display: flex;
                flex-direction: column;
                gap: 1em;
                width: 100%;
                margin-block: 1em;
                padding: 1em;
                line-height: 1.5em;
                background: var(--iai-silver-color-light);
                border-radius: 0.5em;
            }
            iai-silver-responses-list article p {
                margin: 0;
            }
            iai-silver-responses-list article .demo-tag {
                max-width: 100%;
            }
            iai-silver-responses-list article .theme-tag button {
                text-align: start;
            }
            iai-silver-responses-list article header,
            iai-silver-responses-list article footer {
                display: flex;
                align-items: center;
                gap: 0.5em;
                font-size: 0.9em;
                flex-wrap: wrap;
            }
            iai-silver-responses-list article header {
                justify-content: space-between;
            }
            iai-silver-responses-list article header .header-group {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 0.5em;
            }
            iai-silver-responses-list article footer iai-silver-tag .tag {
                background: var(--iai-silver-color-mid-light);
                border: none;
            }
            iai-silver-responses-list iai-virtual-list {
                height: 50em;
            }
            iai-silver-responses-list multi-answers-list {
                display: flex;
                gap: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.responses = [];
        this.responsesTotal = 0;
        this.filteredTotal = 0;
        this.handleScrollEnd = () => {};
        this.isLoading = false;
        this.highlightedText = "";
        this.handleThemeTagClick = () => {};
        
        this.applyStaticStyles("iai-silver-responses-list", ResponsesList.styles);
    }

    render() {
        return html`
            <iai-silver-panel>
                <div slot="content">
                    <iai-silver-title
                        .text=${`Responses (${this.filteredTotal})`}
                        .subtext=${"All responses to this question"}
                        .level=${2}
                    ></iai-silver-title>

                    <iai-virtual-list
                        style=${this.isLoading && this.responses.length === 0
                            ? "height: auto;"
                            : ""
                        }
                        .data=${this.responses}
                        .renderItem=${(response, index) => html`
                            <article class=${index === this.responses.length-1
                                ? "last-item"
                                : ""
                            }>
                                <header>
                                    ${response.demoData.length > 0 || response.evidenceRich ? html`
                                        <div class="header-group">
                                            ${response.demoData
                                                ? response.demoData.map(data => html`
                                                    <iai-silver-tag
                                                        class="demo-tag"
                                                        .text=${data}
                                                    ></iai-silver-tag>
                                                `)
                                                : ""
                                            }
                                            ${response.evidenceRich
                                                ? html`
                                                    <iai-silver-tag
                                                        .icon=${"diamond"}
                                                        .text=${"Evidence rich"}
                                                        .status=${"Closed"}
                                                    ></iai-silver-tag>
                                                `
                                                : ""
                                            }
                                        </div>
                                    ` : ""}

                                    <small>
                                        ID: ${response.id || "Not Available"}
                                    </small>
                                </header>
                                
                                ${response.text ? html`
                                    <p>
                                        ${this.highlightedText
                                            ? unsafeHTML(this.getHighlightedText(response.text, this.highlightedText))
                                            : response.text
                                        }
                                    </p>
                                ` : ""}

                                ${response.multiAnswers.length > 0 ? html`
                                    <ul class="multi-answers-list">
                                        ${response.multiAnswers.map(answer => html`
                                            <iai-silver-tag
                                                .text=${answer}
                                            ></iai-silver-tag>
                                        `)}
                                    </ul>
                                ` : ""}
                                
                                ${response.themes.length > 0 ? html`
                                    <footer>
                                        <small>
                                            Themes:
                                        </small>
                                        ${response.themes.map((theme) => html`
                                            <iai-silver-button
                                                class="theme-tag"
                                                @click=${() => this.handleThemeTagClick(theme.id)}
                                                .text=${theme.text}
                                            ></iai-silver-button>
                                        `)}
                                    </footer>
                                ` : ""}
                            </article>
                        `}
                        .handleScrollEnd=${this.handleScrollEnd}
                    ></iai-virtual-list>

                    ${this.isLoading
                        ? html`<iai-loading-indicator></iai-loading-indicator>`
                        : ""
                    }
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-silver-responses-list", ResponsesList);