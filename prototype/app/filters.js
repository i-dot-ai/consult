//
// For guidance on how to create filters see:
// https://prototype-kit.service.gov.uk/docs/filters
//

const govukPrototypeKit = require('govuk-prototype-kit')
const addFilter = govukPrototypeKit.views.addFilter


addFilter('filter', (data, keywords) => {
  return data.filter((item) => {
    return !keywords || item.toLowerCase().indexOf(keywords.toLowerCase()) !== -1;
  });
});
