import { writeFileSync, readdir, existsSync, lstatSync } from "fs";
import path from "path";

import { render } from "@lit-labs/ssr";

import { html } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import DOMPurify from 'dompurify';
import { JSDOM } from "jsdom";

import IaiLitSsrExample from "./consultation_analyser/lit/ssr/IaiLitSsrExample/iai-lit-ssr-example.lit.ssr.mjs";


async function main() {
    await processLitFiles("./");
}

async function processLitFiles(dir) {

    if (process.argv.includes("--runtime")) {
        renderToStdout();
        return;
    }

    readdir(dir, { withFileTypes: true }, (err, files) => {
        if (err) {
            console.error(err);
        }

        for (const file of files) {
            const fullPath = path.join(dir, file.name);

            if (file.isDirectory()) {
                processLitFiles(fullPath);
            } else if (file.name.includes(".lit.ssr")) {
                console.log("building:", fullPath);
                renderToFileSsr(fullPath);
                console.log("build successful");
            }
        }
    })
}

function getFlagValue(flagName) {
    const index = process.argv.indexOf(flagName);
    return index !== -1 ? process.argv[index + 1] : null;
}

function isDirectory(path) {
    return lstatSync(path).isDirectory();
}

async function renderToStdout() {
    const filePath = getFlagValue("--path");
    const props = getFlagValue("--props");
    if (filePath) {
        // stdout gets returned to the view by subprocess
        console.log(await getRenderStringSsr(filePath, props));
    } else {
        console.error("No path value found for the component path");
    }
}


async function getRenderStringSsr(filePath, encprops) {
    if (!existsSync(filePath) || isDirectory(filePath)) {
        console.error("Component path is invalid");
        return "";
    }

    const fileName = getFileNameWithoutExtension(filePath);
    // props are encoded as base64 to parse them inside component, else they will truncate incorrectly
    const renderResult = render(html`${unsafeHTML(`<${fileName} encprops="${encprops || ''}"></${fileName}>`)}`)

    let output = `<div data-comment="ssr-component">`;
    for await (const chunk of renderResult) {
        output += chunk;
    }

    if (!isShadowDomEnabled()) {
        // Render to light DOM
        output = output.replace(/<template shadowroot="open" shadowrootmode="open">/g, "")
        output = output.replace(/<\/template>/g, "");
    }
    output += `</div>`;

    const window = new JSDOM("").window;
    const purify = DOMPurify(window);
    return purify.sanitize(output, { ADD_TAGS: [fileName], ADD_ATTR: ["shadowroot", "shadowrootmode"]});
}

function isShadowDomEnabled() {
    return process.argv.includes("--shadowdom");
}

async function renderToFileSsr(filePath) {
    const props = await getFlagValue("--props");
    const output = await getRenderStringSsr(filePath, props);
    if (output) {
        writeFileSync(getTargetFilePath(filePath), output, "utf8");
    } else {
        console.warn("SSR output is empty")
    }
}

function getTargetFilePath(filePath) {
    return `${path.dirname(filePath)}/${getFileNameWithoutExtension(filePath)}.html`
}

function getFileNameWithoutExtension(filePath) {
    return path.basename(filePath).replace(".lit.ssr.mjs", "").replace(".lit.csr.mjs", "")
}

main();