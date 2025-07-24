import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Panel from '../../Panel/panel.lit.csr.mjs';
import DemographicsCard from '../DemographicsCard/demographics-card.lit.csr.mjs';


export default class DemographicsSection extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: { type: Array },
        themeFilters: { type: Array },
        demoFilters: { type: Object},
        total: { type: Number },

        demoFiltersApplied: { type: Function },
        themeFiltersApplied: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css` 
            iai-demographics-section .cards {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
                max-width: 100%;
                overflow: auto;
            }    
            iai-demographics-section iai-demographics-card {
                flex-grow: 1;
                max-width: 100%;
            }
            .themes-warning .tag {
                width: 100%;
                margin-bottom: 1em;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._MAX_DEMO_ANSWERS = 10;

        // Prop defaults
        this.data = [];
        this.themeFilters = [];
        this.demoFilters = {};
        this.total = 0;

        this.demoFiltersApplied = () => {};
        this.themeFiltersApplied = () => {};
        
        this.applyStaticStyles("iai-demographics-section", DemographicsSection.styles);
    }

    getFilterWarningText() {
        const demoFiltersText = Object
            .values(this.demoFilters)
            .flat(1)
            .filter(Boolean)
            .join(", ");

        const themeFiltersText = this.themeFilters.length
            ? `${this.themeFilters.length} themes`
            : "";

        return [demoFiltersText, themeFiltersText].filter(Boolean).join(", ");
    }

    render() {
        return html`
            <iai-silver-panel>
                <div slot="content">
                    <div class="top-panel">
                        <iai-silver-title
                            .text=${"Demographics"}
                            .subtext=${"Demographic breakdown for this question"}
                            .icon=${"group"}
                            .level=${2}
                        ></iai-silver-title>

                        ${this.themeFiltersApplied() || this.demoFiltersApplied()
                            ? html`
                                <iai-silver-tag
                                    class="themes-warning"
                                    .text=${"Active theme analysis filters"}
                                    .subtext=${`Showing data for ${this.total.toLocaleString()} responses (filtered by: ${this.getFilterWarningText()})`}
                                    .icon=${"report"}
                                    .status=${"Analysing"}
                                ></iai-silver-tag>
                            `
                            : ""
                        }

                        <div class="cards">
                            ${Object.keys(this.data).map(category => {
                                return Object.values(this.data[category]).length <= this._MAX_DEMO_ANSWERS
                                    ? html`
                                        <iai-demographics-card
                                            .title=${this.toTitleCase(category)}
                                            .data=${this.data[category]}
                                        ></iai-demographics-card>
                                    ` : ""})}
                        </div>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-demographics-section", DemographicsSection);