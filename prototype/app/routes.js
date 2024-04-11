//
// For guidance on how to create routes see:
// https://prototype-kit.service.gov.uk/docs/create-routes
//

const govukPrototypeKit = require('govuk-prototype-kit')
const router = govukPrototypeKit.requests.setupRouter()

router.post('/upload-file', (request, response) => {
    const isJsonFile = request.session.data.file?.includes('.js');
    if (isJsonFile) {
        request.session.data.schemaErrors = [];
        response.redirect('/upload-success');
    } else {
        request.session.data.schemaErrors = [
            'Line 10: Invalid property',
            'Line 20: Missing property "Answer"'
        ];
        response.redirect('/upload');
    }
});
