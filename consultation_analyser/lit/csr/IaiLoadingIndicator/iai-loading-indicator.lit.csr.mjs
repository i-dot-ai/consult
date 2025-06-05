import { html, css } from 'lit';

import IaiLitBase from '../../IaiLitBase.mjs';
import IaiIcon from '../questionsArchive/IaiIcon/iai-icon.mjs';


export default class IaiLoadingIndicator extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-loading-indicator .spinner {
                display: flex;
                justify-content: center;
                animation-name: spin;
                animation-duration: 1s;
                animation-iteration-count: infinite;
                animation-timing-function: ease-in-out;
            }
            iai-loading-indicator .spinner iai-icon .material-symbols-outlined {
                font-size: 3em;
            }

            @keyframes spin {
                from {
                    transform:rotate(0deg);
                }
                to {
                    transform:rotate(360deg);
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        
        this.applyStaticStyles("iai-loading-indicator", IaiLoadingIndicator.styles);
    }

    render() {
        return html`
            <div class="spinner">
                <iai-icon
                    name="progress_activity"
                    .opsz=${48}
                    .color=${"var(--iai-colour-pink)"}
                ></iai-icon>
            </div>
        `;
    }
}
customElements.define("iai-loading-indicator", IaiLoadingIndicator);