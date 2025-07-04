import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class IaiCheckboxInput extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        inputId: { type: String },
        label: { type: String },
        hideLabel: { type: Boolean },
        checked: {type: Boolean },
        value: { type: String },
        handleChange: { type: Function },
        name: {type: String},
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-checkbox-input .govuk-radios__item:last-child,
            iai-checkbox-input .govuk-radios__item:last-of-type {
                margin-bottom: 10px;
            }
            iai-checkbox-input .govuk-radios__label, .govuk-radios__hint {
                padding-bottom: 0;
            }
        `
    ]

    constructor() {
        super();
        this.inputId = "";
        this.hideLabel = false;
        this.label = "";
        this.checked = false;
        this.value = "";
        this.handleChange = () => {};
        this.name = "";

        this.applyStaticStyles("iai-checkbox-input", IaiCheckboxInput.styles);
    }

    updated(changedProps) {
        if (changedProps.has("checked")) {
            this.querySelector("input").checked = this.checked;
        }
    }

    render() {
        return html`
            <div class="govuk-checkboxes__item">
                <input
                    type="checkbox"
                    class="govuk-checkboxes__input"
                    id=${this.inputId}
                    name=${this.name}
                    value=${this.value}
                    @change=${this.handleChange}
                >
                <label
                    class="govuk-label govuk-checkboxes__label"
                    for=${this.inputId}
                >
                    ${this.hideLabel ? "" : this.label}
                </label>
            </div>
        `
    }
}
customElements.define("iai-checkbox-input", IaiCheckboxInput);