import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiSelectInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        name: {type: String},
        label: { type: String },
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
        this.placeholder = "Select an option";
        this.value = "";
        this.handleChange = () => {};

        this.applyStaticStyles("iai-select-input", IaiSelectInput.styles);
    }

    render() {
        return html`
            <div class="govuk-form-group">
                <label class="govuk-label" for=${this.inputId}>
                    ${this.label}
                </label>
                <select
                    class="govuk-select"    
                    id=${this.inputId}    
                    name=${this.name}
                    value=${this.value}
                    @change=${this.handleChange}
                >
                    ${[ // Add placeholder empty option to options
                        { value: "", text: this.placeholder },
                        ...this.options
                    ].map(option => html`
                        <option
                            value=${option.value}
                            ?selected=${option.value === this.value}
                        >
                            ${option.text}
                        </option>
                    `)}
                </select>
            </div>
        `
    }
}
customElements.define("iai-select-input", IaiSelectInput);