if (!document.querySelector(`link[data-id="govuk-style"]`)) {
    const url = "https://cdn.jsdelivr.net/npm/govuk-frontend@5.10.2/dist/govuk/govuk-frontend.min.css";
    document.head.innerHTML += `<link data-id="govuk-style" type="text/css" rel="stylesheet" href=${url}>`;
}