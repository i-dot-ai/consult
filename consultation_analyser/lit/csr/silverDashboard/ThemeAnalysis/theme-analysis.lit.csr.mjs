import { html, css } from 'lit';

import IaiLitBase from '../../../IaiLitBase.mjs';
import IaiAnimatedNumber from '../../IaiAnimatedNumber/iai-animated-number.lit.csr.mjs';
import IaiProgressBar from '../../IaiProgressBar/iai-progress-bar.lit.csr.mjs';
import IaiDataTable from '../../IaiDataTable/iai-data-table.lit.csr.mjs';
import Button from '../Button/button.lit.csr.mjs';
import IaiIcon from '../../IaiIcon/iai-icon.mjs';
import SelectInput from '../inputs/SelectInput/select-input.lit.csr.mjs';
import ThemesTable from '../ThemesTable/themes-table.lit.csr.mjs';
import Title from '../Title/title.lit.csr.mjs';
import IconTile from '../IconTile/icon-tile.lit.csr.mjs';
import IaiIconButton from '../../questionsArchive/IaiIconButton/iai-icon-button.lit.csr.mjs';
import IaiCsvDownload from '../../IaiCsvDownload/iai-csv-download.lit.csr.mjs';
import ThemeFiltersWarning from '../ThemeFiltersWarning/theme-filters-warning.lit.csr.mjs';
import MultiDropdown from '../inputs/MultiDropdown/multi-dropdown.lit.csr.mjs';


export default class ThemeAnalysis extends IaiLitBase {
    static properties = {
        ...IaiLitBase.properties,
        consultationSlug: { type: String },
        themes: { type: Array },
        totalResponses: { type: Number },
        themeFilters: { type: Array },
        updateThemeFilters: { type: Function },
    }

    static styles = [
        IaiLitBase.styles,
        css`
            iai-theme-analysis div[slot="content"] {
                padding-block: 0.5em;
            }
            iai-theme-analysis iai-silver-icon-tile {
                font-size: 0.8em;
            }
            iai-theme-analysis .theme-title {
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-analysis .percentage-cell {
                gap: 0.5em;
                display: flex;
                align-items: center;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar {
                flex-grow: 1;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .container {
                border-radius: 0.5em;
                background: var(--iai-silver-color-mid);
                border: none;
                opacity: 0.7;
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .bar {
                height: 0.5em;
                border-top-left-radius: 0.5em;
                border-bottom-left-radius: 0.5em;
                background: var(--iai-silver-color-dark);
            }
            iai-theme-analysis .percentage-cell iai-progress-bar .bar.full {
                border-radius: 0.5em;
            }
            iai-theme-analysis iai-silver-button button {
                width: max-content;
                display: flex;
                align-items: center;
                padding-inline: 0.5em;
                gap: 0.5em;
                font-weight: bold;
                color: var(--iai-silver-color-text);
            }
            iai-theme-analysis .filters-row {
                display: grid;
                gap: 1em;
            }
            iai-theme-analysis .total-themes {
                display: flex;
                flex-direction: column;    
                max-height: max-content;
                padding: 1em;
                font-size: 0.8em;
                white-space: nowrap;
                background: #fcf1f6;
                border-radius: 0.5em;
            }
            iai-theme-analysis .total-themes span {
                font-size: 1.5em;
                font-weight: bold;
            }
            iai-theme-analysis .filters-row {
                margin-bottom: 1em;
                background: var(--iai-silver-color-light);
                padding: 1em;
                border-radius: 0.5em;
            }
            iai-theme-analysis .filters {
                display: flex;
                flex-wrap: wrap;
                gap: 1em;
                align-items: center;
            }
            iai-theme-analysis .filters iai-silver-select-input{
                white-space: nowrap;
            }
            iai-theme-analysis .top-panel {
                margin-bottom: 2em;
            }
            iai-theme-analysis .filters select.govuk-select {
                font-size: 0.9em;
                background: var(--iai-silver-color-light-darker);
            }
            iai-theme-analysis iai-multi-dropdown button {
                background: var(--iai-silver-color-light-darker) !important;
            }
            iai-theme-analysis .export-button button {
                padding-block: 0.2em;
            }
            iai-theme-analysis .filters .demographics-title .icon-container {
                margin: 0;
                color: var(--iai-silver-color-dark);
            }
            iai-theme-analysis .filters .govuk-form-group:has(select){
                margin: 0;
            }
            iai-theme-analysis .info-container {
                display: flex;
                justify-content: space-between;
            }
            @media (min-width: 40.0625em) {
                .govuk-form-group {
                    margin-bottom: 0;
                }
            }
        `
    ]

    constructor() {
        super();
        this.contentId = this.generateId();
        this._NUMBER_ANIMATION_DURATION = 1000;

        this.consultationSlug = "";
        this.themes = [];
        this.totalResponses = 0;
        this.themeFilters = [];
        this.updateThemeFilters = () => {};

        this.applyStaticStyles("iai-theme-analysis", ThemeAnalysis.styles);
    }

    render() {
        return html`
            <iai-silver-panel>
                <div slot="content">
                    <div class="top-panel">
                        <iai-silver-title
                            .text=${"Theme analysis"}
                            .variant=${"secondary"}
                            .icon=${"lan"}
                            .aside=${html`
                                <iai-csv-download
                                    .fileName=${`theme_mentions_for_${this.consultationSlug}.csv`}
                                    .variant=${"silver"}
                                    .data=${
                                        this.themes.map(theme => ({
                                            "Theme Name": theme.title,
                                            "Theme Description": theme.description,
                                            "Mentions": theme.mentions,
                                            "Percentage": this.getPercentage(theme.mentions, this.totalResponses),
                                        }))
                                    }
                                >
                                </iai-csv-download>
                            `}
                        ></iai-silver-title>

                        <div class="info-container">
                            <small>
                                Total Themes
                                <span>${this.themes.length}<span>
                            </small>

                            <small>
                                <!-- optional microcopy -->
                            </small>
                        </div>
                    </div>

                    <iai-themes-table
                        .themes=${this.themes}
                        .themeFilters=${this.themeFilters}
                        .setThemeFilters=${this.updateThemeFilters}
                        .totalResponses=${this.totalResponses}
                    ></iai-themes-table>
                </div>
            </iai-silver-panel>
        `;
    }
}
customElements.define("iai-theme-analysis", ThemeAnalysis);
