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

## Server-Side Rendering at Build Time
### Build:
Run the below command to build SSR components into static html files:
```
npm run build-lit-ssr
```

This will generate an .html file next to each component that has ".lit.ssr" in its name, which can be included and served in a Jinja template.

### How to:
Create a new .mjs file with your Lit component, ideally extend from IaiLitBase base class.

Include ".lit.ssr" in the name of your component file. Ex:
```
some-component.lit.ssr.mjs
```

In the Jinja template, use resulting html file as below:

```
{% include "ssr/IaiLitSsrExample/iai-lit-ssr-example.html" %}
```

### Passing props from template context
Recommended way is to use the Server-Side Rendering at Runtime approach for passing props from a Jinja template context.

Regardless, --props flag can be used to pass props as a base64 encrypted JSON string.


## Build Script Flags
The build script "build-lit.mjs" can take several flags:
```
npm run build-lit-ssr -- --shadowdom --runtime --path <path-to-component.mjs>
```

### shadowdom
Renders SSR components into shadow DOM if passed

### runtime
Used to specify the command is called at runtime, so that the render result is output to stdout rather than a file.

### path
Used to specify a component path so only that component is built. Must be used wih runtime enabled to have an effect.