import { html, css } from 'lit';

import IaiIcon from '../../../IaiIcon/iai-icon.mjs';
import IaiIconButton from '../../../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';
import IaiTextInput from '../../../inputs/IaiTextInput/iai-text-input.lit.csr.mjs';

import IaiLitBase from '../../../../IaiLitBase.mjs';


export default class SearchBox extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: { type: String },
        label: { type: String },
        placeholder: { type: String },
        value: { type: String },
        hideLabel: { type: Boolean },
        handleInput: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-search-box .search-box-container {
                position: relative;
            }
            iai-silver-search-box .search-box-container input {
                padding-left: 2.5em;
                border-radius: 0.5em;
                background: var(--iai-silver-color-light);
                border: none;
            }
            iai-silver-search-box .search-box-container iai-icon {
                position: absolute;
                left: 0.5em;
                bottom: 0.5em;
            }
            iai-silver-search-box .clear-button {
                position: absolute;
                top: 50%;
                right: 2em;
                z-index: 1;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.placeholder = "";
        this.value = "";
        this.hideLabel = true;
        this.handleInput = () => {};

        this.applyStaticStyles("iai-silver-search-box", SearchBox.styles);
    }

    render() {
        return html`
            <div class="search-box-container">
                <iai-text-input
                    .inputId=${this.inputId}
                    .name=${this.name}
                    .label=${this.label}
                    .placeholder=${this.placeholder}
                    .value=${this.value}
                    .hideLabel=${this.hideLabel}
                    .handleInput=${this.handleInput}
                ></iai-text-input>

                <iai-icon
                    name="search"
                    .color=${"var(--iai-colour-text-secondary)"}
                    .fill=${0}
                ></iai-icon>

                ${this.value
                    ? html`
                        <iai-icon-button
                            class="clear-button"
                            .title="Clear search"
                            @click=${() => {
                                this.value = "";
                                this.handleInput({target: {value: ""}})
                                this.querySelector("input").value = "";
                            }}
                        >
                            <iai-icon
                                slot="icon"
                                .name=${"close"}
                                .color=${"var(--iai-silver-color-text)"}
                            ></iai-icon>
                        </iai-icon-button>
                    `
                    : ""
                }
            </div>
        `;
    }
}
customElements.define("iai-silver-search-box", SearchBox);