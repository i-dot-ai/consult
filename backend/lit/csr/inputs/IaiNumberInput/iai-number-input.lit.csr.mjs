import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiNumberInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: {type: String},
        label: { type: String },
        placeholder: { type: String },
        value: { type: String },
        handleInput: { type: Function },
        horizontal: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-number-input .horizontal {
                display: flex;
                align-items: center;
                gap: 0.5em;
            }
            iai-number-input .horizontal label {
                margin: 0;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.placeholder = "";
        this.value = "";
        this.handleChange = () => {};
        this.horizontal = false;

        this.applyStaticStyles("iai-number-input", IaiNumberInput.styles);
    }

    render() {
        return html`
            <div class=${this.horizontal ? "horizontal" : ""}>
                <label class="govuk-label govuk-label--m" for=${this.inputId}>
                    ${this.label}
                </label>
                <input
                    type="number"
                    class="govuk-input"
                    id=${this.inputId}
                    name=${this.name}
                    placeholder=${this.placeholder}
                    value=${this.value}
                    @input=${this.handleInput}
                />
            </div>
        `
    }
}
customElements.define("iai-number-input", IaiNumberInput);