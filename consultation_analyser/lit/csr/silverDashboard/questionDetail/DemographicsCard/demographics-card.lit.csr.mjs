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
                max-height: 40em;
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
                gap: 1.5em;
                margin: 0;
                padding-left: 0;
                font-weight: bold;
                font-size: 0.9em;
            }
            iai-demographics-card li {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-direction: column;
                list-style: none;
                line-height: 1.5em;
                gap: 0.5em;
            }
            iai-demographics-card li>* {
                width: 100%;
                word-wrap: break-word;
            }
            iai-demographics-card li .percentage {
                font-size: 0.8em;
                color: rgba(0, 0, 0, 0.5);
            }
            iai-demographics-card li .count {
                font-size: 1.2em;
            }
            iai-demographics-card li {
                font-size: 0.9em;
                color: rgba(0, 0, 0, 0.6);
            }
            iai-demographics-card .info {
                display: flex;
                gap: 0.5em;
            }
            iai-demographics-card .label {
                font-size: 0.9em;
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
                height: 0.6em;
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
                        const percentage = this.getPercentage(count, this._totalCount);

                        return html`
                            <li>
                                <div class="info">
                                    <span class="label">
                                        ${label}
                                    </span>
                                    <span class="count">
                                        ${count.toLocaleString()}
                                    </span>
                                    <span class="percentage">
                                        ${percentage}%
                                    </span>
                                </div>

                                <div>
                                    <iai-silver-progress-bar
                                        .value=${percentage}
                                    ></iai-silver-progress-bar>
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