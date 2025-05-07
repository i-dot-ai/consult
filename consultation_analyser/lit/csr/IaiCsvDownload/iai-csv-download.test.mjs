import { expect, fixture, html } from '@open-wc/testing';
import "./iai-csv-download.lit.csr.mjs";
import { DEFAULT_DATA } from './testData.mjs';


describe('iai-csv-download', () => {
  it('renders filename', async () => {
    const fileName = "test_filename.csv";

    const el = await fixture(html`
      <iai-csv-download
        .data=${DEFAULT_DATA}
        fileName=${fileName}
      ></iai-csv-download>
    `);
    expect(el.querySelector("a").download).to.equal(fileName);
  });

  it('renders all data as base64 encoded csv in href', async () => {
    const fileName = "test_filename.csv";

    const el = await fixture(html`
      <iai-csv-download
        .data=${DEFAULT_DATA}
        fileName=${fileName}
      ></iai-csv-download>
    `);
    const resultBase64 = el.querySelector("a").href.replace("data:text/csv;base64,", "");
    const decodedResultCsv = atob(resultBase64);

    for (const row of DEFAULT_DATA) {
      for (const [key, value] of Object.entries(row)) {
        expect(decodedResultCsv).to.include(key);
        expect(decodedResultCsv).to.include(value);
      }
    }
  });
});