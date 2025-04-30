import { expect, fixture, html } from '@open-wc/testing';
import "./iai-data-table.lit.csr.mjs";
import { DEFAULT_DATA, RESERVED_KEYS } from './testData.mjs';


describe('iai-data-table', () => {

  it('renders data', async () => {
    const el = await fixture(html`
      <iai-data-table
        .data=${DEFAULT_DATA}
      ></iai-expanding-text>
    `);
    
    for (const row of DEFAULT_DATA) {
      for (const [header, cellValue] of Object.entries(row)) {
        if (!RESERVED_KEYS.includes(header)) {
          expect(el.outerHTML.trim()).to.contain(header);
          expect(el.outerHTML.trim()).to.contain(cellValue);  
        }
      }
    }
  });

  it('sorts data', async () => {
    const columnToSort = "Theme name";
    let bodyRowEls;

    const el = await fixture(html`
      <iai-data-table
        .data=${DEFAULT_DATA}
      ></iai-expanding-text>
    `);

    // No sorting applied initially
    el.querySelectorAll(".header-button").forEach(headerButtonEl => {
      expect(headerButtonEl.classList.contains("ascending")).to.equal(false);
      expect(headerButtonEl.classList.contains("descending")).to.equal(false);
    })

    // Rows are unsorted, same order as test data
    const regularRowData = DEFAULT_DATA.filter(row => !row._bottomRow);
    bodyRowEls = el.querySelectorAll("tbody tr:not(.bottom-row)");
    for (let i=0; i<bodyRowEls.length; i++) {
      const cellContent = bodyRowEls[i].querySelector("td").textContent.trim()[0];
      const dataContent = regularRowData[i][columnToSort][0];
      expect(cellContent).to.equal(dataContent);
    }

    // Get the header to click for sorting
    const headerButton = el.querySelector(".header-button");
    expect(headerButton.textContent.trim()).to.equal(columnToSort);

    // click to apply ascending sort
    headerButton.click();
    await el.updateComplete;
    expect(headerButton.classList.contains("ascending")).to.equal(true);
    expect(el.querySelector("tbody tr:not(.bottom-row)").textContent.trim()[0]).to.equal("B")

    // reverse ascending cell data for comparison later
    const ascendingCells = el.querySelectorAll("tbody tr:not(.bottom-row)");
    const descendingCells = [...ascendingCells]
                              .map(cell => cell.querySelector("td").textContent.trim())
                              .reverse();

    // click again to apply descending sort
    headerButton.click();
    await el.updateComplete;
    await el.updateComplete;
    expect(headerButton.classList.contains("descending")).to.equal(true);
    expect(headerButton.classList.contains("ascending")).to.equal(false); 

    // check if cells are in descending order
    bodyRowEls = el.querySelectorAll("tbody tr:not(.bottom-row)");
    for (let i=0; i<bodyRowEls.length; i++) {
      const cellContent = bodyRowEls[i].querySelector("td").textContent.trim()[0];
      const dataContent = descendingCells[i][0];
      expect(cellContent).to.equal(dataContent);
    }
  });
});