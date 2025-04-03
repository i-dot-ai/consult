import { writeFileSync, readFileSync, readdir, existsSync, lstatSync } from "fs";
import path from "path";

import { render } from "@lit-labs/ssr";

import { html } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import { IaiLitSsr } from "./consultation_analyser/consultations/jinja2/components/iai-lit-test/iai-lit-ssr.lit.ssr.mjs";


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
            } else if (file.name.includes(".lit")) {
                if (file.name.includes(".ssr")) {
                    console.log("building:", fullPath);
                    renderToFileSsr(fullPath);
                    console.log("build successful");
                } else if (file.name.includes(".csr")) {
                    console.log("building:", fullPath);
                    renderToFileCsr(fullPath);
                    console.log("build successful");
                }
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


async function getRenderStringSsr(filePath, propsString) {
    if (!existsSync(filePath) || isDirectory(filePath)) {
        console.error("Component path is invalid");
        return "";
    }

    const fileName = getFileNameWithoutExtension(filePath);
    // encode props as base64 to parse them inside component, else they will truncate incorrectly
    const renderResult = render(html`${unsafeHTML(`<${fileName} propsString="${btoa(propsString)}"></${fileName}>`)}`)

    let output = "";
    for await (const chunk of renderResult) {
        output += chunk;
    }
    return output;
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

async function renderToFileCsr(filePath) {
    const componentCode = readFileSync(filePath, "utf-8");

    const result = `<script type="module">\n${componentCode}\n</script>`;
    
    let output = "";
    for await (const chunk of result) {
        output += chunk;
    }
    
    writeFileSync(getTargetFilePath(filePath), output, "utf8");
}

main();