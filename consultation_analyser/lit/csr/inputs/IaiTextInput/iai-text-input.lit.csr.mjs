import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiTextInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: {type: String},
        label: { type: String },
        hideLabel: {type: Boolean},
        placeholder: { type: String },
        value: { type: String },
        handleInput: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css``
    ]

    constructor() {
        super();
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.hideLabel = false;
        this.placeholder = "";
        this.value = "";
        this.handleChange = () => {};

        this.applyStaticStyles("iai-text-input", IaiTextInput.styles);
    }

    render() {
        return html`
            <label
                for=${this.inputId}
                class=${
                    "govuk-label govuk-label--m"
                    + (this.hideLabel ? " visually-hidden" : "")
                }
            >
                ${this.label}
            </label>
            <input
                type="text"
                class="govuk-input"
                id=${this.inputId}
                name=${this.name}
                placeholder=${this.placeholder}
                value=${this.value}
                @input=${this.handleInput}
            />
        `
    }
}
customElements.define("iai-text-input", IaiTextInput);