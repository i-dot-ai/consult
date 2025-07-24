import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiSelectInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: {type: String},
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
            .horizontal {
                display: flex;
                align-items: center;
                gap: 0.5em;
            }
            .horizontal label {
                margin: 0;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.name = "";
        this.label = "";
        this.hideLabel = true;
        this.placeholder = "";
        this.options = [];
        this.value = "";
        this.handleChange = () => {};
        this.horizontal = false;

        this.applyStaticStyles("iai-select-input", IaiSelectInput.styles);
    }

    render() {
        return html`
            <div class=${"govuk-form-group" + (this.horizontal ? " horizontal" : "")}>
                <label
                    class=${"govuk-label" + (this.hideLabel ? " visually-hidden" : "")}
                    for=${this.inputId}
                >
                    ${this.label}
                </label>
                <select
                    class="govuk-select"
                    .id=${this.inputId}
                    .name=${this.name}
                    .value=${this.value}
                    @change=${this.handleChange}
                >
                    ${[ // Add placeholder empty option to options
                        { value: "", text: this.placeholder },
                        ...this.options
                    ].map(option => {
                        if (!option.value && !this.placeholder) {
                            return "";
                        }
                        return html`
                            <option
                                .value=${option.value}
                                ?selected=${option.value === this.value}
                            >
                                ${option.text}
                            </option>
                        `})
                    }
                </select>
            </div>
        `
    }
}
customElements.define("iai-select-input", IaiSelectInput);