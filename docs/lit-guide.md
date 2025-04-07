# Lit Element Guide

## Introduction
Lit components can be used alongside Django, served through Jinja templates.

Components can be bundled and served to be rendered on the client side, built as static HTML to be included in Jinja templates, or be built at runtime and served from the view as template context.

Below command builds both CSR and SSR components.

```
npm run build-lit
```

## Client-Side Rendering
### Build:
Run the below command to build CSR bundle only:
```
npm run build-lit-csr
```

This will use Rollup to bundle client-side Lit components. Bundle builds to "/frontend/lit/bundle.js".

### How to:
Create a new .mjs file with your Lit component, ideally extend from IaiLitBase base class.

Add your component to "/consultation_analyser/lit/csr/index.js" similar to below:
```
import IaiLitCsrExample from "./IaiLitCsrExample/iai-lit-csr-example.lit.csr.mjs";
```

Make sure component bundle is imported somewhere in the Jinja template:
```  
<script type="module" src="{{ static("lit/bundle.js") }}" ></script>
```

Use your component anywhere in your markup:
```
<iai-lit-csr-example></iai-lit-csr-example>
```

### Passing props from template context
You can pass props to your CSR component by rendering an "encprops" attribute with a base64 encoded JSON string:

Django View:
```
return render(request, "some/template.html", {"someprops": base64.b64encode(b'{"foo": "bar"}').decode()})
```

Jinja Template:
```
<iai-lit-csr-example encprops="{{ testprops | safe }}"></iai-lit-csr-example>
```