import { html, css } from 'lit';

import IaiSelectInput from '../../../inputs/IaiSelectInput/iai-select-input.lit.csr.mjs';

import IaiLitBase from '../../../../IaiLitBase.mjs';


export default class SelectInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: { type: String },
        label: { type: String },
        hideLabel: { type: Boolean },
        placeholder: { type: String },
        options: { type: Array },
        value: { type: String },
        handleInput: { type: Function },
        horizontal: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-silver-select-input iai-select-input select.govuk-select {
                border: none;
                background: var(--iai-silver-color-light);
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
        this.hideLabel = true;
        this.placeholder = "";
        this.options = [];
        this.value = "";
        this.handleChange = () => {};
        this.horizontal = false;

        this.applyStaticStyles("iai-silver-select-input", SelectInput.styles);
    }

    render() {
        return html`
            <iai-select-input
                .inputId=${this.inputId}
                .name=${this.name}
                .label=${this.label}
                .hideLabel=${this.hideLabel}
                .placeholder=${this.placeholder}
                .options=${this.options}
                .value=${this.value}
                .handleChange=${this.handleChange}
                .horizontal=${this.horizontal}
            ></iai-select-input>
        `
    }
}
customElements.define("iai-silver-select-input", SelectInput);