const {execSync} = require("child_process");


function renderLitSsr(path, props) {
    const command = `npm run build-lit-ssr -- --runtime --path ${path} ${props ? `--props ${btoa(JSON.stringify(props))}` : ""}`;
    const stdout = execSync(command, { encoding: "utf-8" }).trim();
    const componentStartIndex = stdout.indexOf(`<div data-comment="ssr-component">`);
    return stdout.slice(componentStartIndex);
}


module.exports = {
    renderLitSsr,
}