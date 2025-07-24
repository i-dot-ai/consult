import { html, css } from 'lit';
import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Button from '../../Button/button.lit.csr.mjs';


export default class MultiDropdown extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        text: { type: String },
        options: { type: Array }, //  { id, checked, title, handleClick }

        _panelVisible: { type: Boolean },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-multi-dropdown label,
            iai-multi-dropdown select,
            iai-multi-dropdown input {
                //font-size: 0.9em !important;
            }
            iai-multi-dropdown label {
                cursor: pointer;
                word-break: break-word;
                line-height: 1.5em;
            }
            iai-multi-dropdown .filters {
                display: flex;
                gap: 1em;
                width: 100%;
                flex-direction: column;
            }
            iai-multi-dropdown input[type="checkbox"] {
                width: auto;
                filter: grayscale(0.5) hue-rotate(75deg);
                cursor: pointer;
            }

            iai-multi-dropdown ul {
                list-style: none;
                padding-left: 0;
                margin: 0;
            }
            iai-multi-dropdown ul li {
                display: flex;
                gap: 0.5em;
                justify-content: flex-start;
                margin-bottom: 0.5em;
            }
            
            iai-multi-dropdown .popup-button .popup-panel {
                position: absolute;
                top: 2em;
                width: max-content;
                max-width: 80vw;
                max-height: 20em;
                overflow: auto;
                right: 0;
                background: white;
                padding: 1em;
                margin: 0;
                z-index: 2;
                border: 1px solid var(--iai-silver-color-mid);
                border-radius: 0.5em;
                opacity: 1;
                transition: opacity 0.3s ease-in-out;
                box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 6px -1px, rgba(0, 0, 0, 0.1) 0px 2px 4px -2px;
            }
            iai-multi-dropdown .popup-button {
                position: relative;
            }
            iai-multi-dropdown .popup-button .popup-panel.left-placement {
                right: unset;
                left: 0;
            }
            iai-multi-dropdown .popup-panel .content {
                display: flex;
                align-items: center;
                gap: 1em;
            }
            iai-multi-dropdown .popup-button .icon-container {
                margin-bottom: 0.5em;
            }
            iai-multi-dropdown .popup-button iai-silver-title {
                color: var(--iai-silver-color-dark);
                cursor: pointer;
            }
            iai-multi-dropdown .popup-button .popup-button__body {
                position: relative;
            }
            iai-multi-dropdown .popup-button .popup-button__body iai-silver-button button {
                width: 100%;    
                line-height: 2em;
                background: var(--iai-silver-color-light);
                border: none;
                border-radius: 0.3em;
            }
            iai-multi-dropdown .popup-button .popup-button__text {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.title = "";
        this.text = "";
        this.options = [];

        this._panelVisible = false;
        this._leftPlacement = false;
        
        this.applyStaticStyles("iai-multi-dropdown", MultiDropdown.styles);
    }

    handleOutsideClick = (e) => {
        if (!this.contains(e.target)) {
            this._panelVisible = false;
        }
    }

    connectedCallback() {
        super.connectedCallback();
        this.setupPanelListeners(window.addEventListener);;
    }

    disconnectedCallback() {
        this.setupPanelListeners(window.removeEventListener);
        super.disconnectedCallback();
    }

    setupPanelListeners = (func) => {
        ["click", "touchstart"].forEach(eventName => {
            func(eventName, this.handleOutsideClick)
        })
    }

    isLeftPlaced = () => {
        const buttonEl = this.querySelector("iai-silver-button");
        if (!buttonEl) {
            return;
        }

        const rect = buttonEl.getBoundingClientRect();

        const elementCenter = rect.left + rect.width / 2;
        const screenCenter = window.innerWidth / 2;

        return elementCenter < screenCenter;
    }

    willUpdate(changedProps) {
        if (changedProps.has("_panelVisible")) {
            this._leftPlacement = this.isLeftPlaced();
        }
    }

    render() {
        return html`
            <div class="popup-button">
                <iai-silver-title
                    .level=${3}
                    .text=${this.title}
                    @click=${() => this._panelVisible = !this._panelVisible}
                ></iai-silver-title>

                <div class="popup-button__body">
                    <iai-silver-button
                        .text=${html`
                            <div class="popup-button__text">
                                <span>
                                    ${this.text}
                                </span>
                                <iai-icon
                                    .name=${"keyboard_arrow_down"}
                                ></iai-icon>
                            </div>
                        `}
                        .handleClick=${() => this._panelVisible = !this._panelVisible}
                    ></iai-silver-button>

                    ${this.options.length > 0 ? html`
                        <div
                            class=${"popup-panel" + (this._leftPlacement ? " left-placement" : "")}
                            style=${`
                                opacity: ${this._panelVisible ? 1 : 0};
                                pointer-events: ${this._panelVisible ? "auto" : "none"};
                            `}
                        >
                            <div class="content">
                                <ul>
                                    ${this.options.map(option => {
                                        const optionId = `${this.contentId}-${option.id.replace(" ", "-")}`;

                                        return html`
                                            <li>
                                                <input
                                                    type="checkbox"
                                                    class="theme-checkbox"
                                                    id=${optionId}
                                                    name=${`multi-dropdown-${this.contentId}`}
                                                    .value=${option.id}
                                                    .checked=${option.checked}
                                                    @click=${option.handleClick}
                                                />
                                                <label for=${optionId}>
                                                    ${option.title}
                                                </label>
                                            </li>
                                        `}
                                    )}
                                </ul>
                            </div>
                        </div>
                    ` : ""}
                </div>
                
            </div>
        `
    }
}
customElements.define("iai-multi-dropdown", MultiDropdown);