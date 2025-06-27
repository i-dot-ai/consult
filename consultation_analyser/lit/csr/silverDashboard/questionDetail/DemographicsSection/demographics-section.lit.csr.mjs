import { html, css } from 'lit';

import IaiLitBase from '../../../../IaiLitBase.mjs';
import Title from '../../Title/title.lit.csr.mjs';
import Panel from '../../Panel/panel.lit.csr.mjs';
import DemographicsCard from '../DemographicsCard/demographics-card.lit.csr.mjs';


export default class DemographicsSection extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        data: { type: Array },
    }

    static styles = [
        IaiLitBase.styles,
        css` 
            iai-demographics-section .cards {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
            }    
            iai-demographics-section iai-demographics-card {
                flex-grow: 1;    
                min-width: max-content;
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();

        // Prop defaults
        this.data = [];
        
        this.applyStaticStyles("iai-demographics-section", DemographicsSection.styles);
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

                        <div class="cards">
                            ${this.data.map(category => html`
                                <iai-demographics-card
                                    .title=${category.title}
                                    .data=${category.data}
                                ></iai-demographics-card>
                            `)}
                        </div>
                    </div>
                </div>
            </iai-silver-panel>
        `
    }
}
customElements.define("iai-demographics-section", DemographicsSection);