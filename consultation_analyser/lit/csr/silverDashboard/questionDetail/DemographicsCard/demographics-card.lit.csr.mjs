import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import ProgressBar from '../../ProgressBar/progress-bar.lit.csr.mjs';


export default class DemographicsCard extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        title: { type: String },
        data: { type: Object }, //  key/value pairs
        _totalCount: { type: Number },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-demographics-card article {
                height: 100%;
                max-height: 15em;
                overflow: auto;
                padding: 1em;
                font-size: 1em;
                color: var(--iai-silver-color-text);
                background: var(--iai-silver-color-light);
                border-radius: 0.5em;
            }
            iai-demographics-card ul {
                display: flex;
                flex-direction: column;
                gap: 0.5em;    
                margin: 0;
                padding-left: 0;
                font-weight: bold;
                font-size: 0.9em;
            }
            iai-demographics-card li {
                display: flex;
                justify-content: space-between;
                align-items: center;
                list-style: none;
            }
            iai-demographics-card li>* {
                width: 50%;
            }
            iai-demographics-card .counts {
                display: flex;
                align-items: center;
                gap: 1em;
                font-weight: normal;
                font-size: 0.8em;
            }
            
            iai-demographics-card iai-silver-progress-bar .container,
            iai-demographics-card iai-silver-progress-bar .container .bar {
                height: 0.5em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.data = {};
        this._totalCount = 0;
        
        this.applyStaticStyles("iai-demographics-card", DemographicsCard.styles);
    }

    updated(changedProps) {
        if (changedProps.has("data")) {
            this._totalCount = Object.values(this.data).reduce( (a, b) => a + b, 0 );
        }
    }

    render() {
        return html`
            <article>
                <iai-silver-title
                    .text=${this.title}
                    .level=${3}
                ></iai-silver-title>

                <ul>
                    ${Object.keys(this.data).map(key => {
                        const label = key;
                        const count = this.data[key];

                        return html`
                            <li>
                                <div>
                                    <span>${label}</span>
                                </div>
                                <div class="counts">
                                    <iai-silver-progress-bar
                                        .value=${this.getPercentage(count, this._totalCount)}
                                    ></iai-silver-progress-bar>
                                    <span>
                                        ${count.toLocaleString()}
                                    </span>
                                </div>
                            </li>
                        `
                    })}
                </ul>
            </article>
        `
    }
}
customElements.define("iai-demographics-card", DemographicsCard);