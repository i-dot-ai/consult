import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiRadioInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        label: { type: String },
        checked: {type: Boolean },
        value: { type: String },
        handleChange: { type: Function },
        name: {type: String},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            .govuk-radios__item {
                margin-bottom: 10px;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.label = "";
        this.checked = false;
        this.value = "";
        this.handleChange = () => {};
        this.name = "";
    }

    render() {
        return html`
            <style>
                iai-radio-input .govuk-radios__item:last-child,
                iai-radio-input .govuk-radios__item:last-of-type {
                    margin-bottom: 10px;
                }
            </style>
        
            <div class="govuk-radios__item">
                <input
                    type="radio"
                    class="govuk-radios__input"
                    id=${this.inputId}
                    name=${this.name}
                    ?checked=${this.checked}
                    value=${this.value}
                    @change=${this.handleChange}
                />

                <label
                    class="govuk-label govuk-radios__label"
                    for=${this.inputId}
                >
                    ${this.label}
                </label>
            </div>
        `
    }
}
customElements.define("iai-radio-input", IaiRadioInput);