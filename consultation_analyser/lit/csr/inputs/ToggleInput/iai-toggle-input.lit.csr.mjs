import { html, css } from 'lit';
import IaiLitBase from '../../../IaiLitBase.mjs';


export default class ToggleInput extends IaiLitBase {
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
            iai-toggle-input {
                --handle-size: 1.2em;
                display: flex;
                gap: 1em;
                align-items: center;
            }
            iai-toggle-input input {
                opacity: 0;
                position: absolute;
                z-index: -1;
            }
            iai-toggle-input label {
                cursor: pointer;
            }
            iai-toggle-input label.slider {
                position: relative;
                display: inline-block;
                width: 3em;
                height: 1.5em;
                background: var(--iai-silver-color-mid);
                border-radius: 5em;
                cursor: pointer;
                transition: background 0.3s ease-in-out;
            }
            iai-toggle-input label.slider:before {
                content: "";
                position: absolute;
                height: var(--handle-size);
                width: var(--handle-size);
                border-radius: 50%;
                background: white;
                left: calc(var(--handle-size) / 5);
                top: calc(var(--handle-size) / 9);
                transition: left 0.3s ease-in-out;
                cursor: pointer;
            }
            iai-toggle-input label.slider:has(input:focus),
            iai-toggle-input label.slider:has(input:focus-visible) {
                outline: 0.3em solid var(--iai-colour-focus);
            }
            iai-toggle-input label.slider:has(input[data-checked="true"]) {
                background: var(--iai-silver-color-dark);
            }
            iai-toggle-input label.slider:has(input[data-checked="true"])::before {
                left: calc(45% + var(--handle-size) / 5);
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

        this.applyStaticStyles("iai-toggle-input", ToggleInput.styles);
    }

    updated(changedProps) {
        if (changedProps.has("checked")) {
            this.querySelector("input").checked = this.checked;
        }
    }

    render() {
        return html`
            <label for=${this.inputId} class=${this.hideLabel ? "visually-hidden" : ""}>
                ${this.label}
            </label>
            <label class="slider" for=${this.inputId}>
                <input
                    type="checkbox"
                    id=${this.inputId}
                    name=${this.name}
                    value=${this.value}
                    @click=${this.handleChange}
                    data-checked=${this.checked ? "true" : "false"}
                >
            </label>
        `
    }
}
customElements.define("iai-toggle-input", ToggleInput);