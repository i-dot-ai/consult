export default {
    files: "**/lit/csr/**/*.test.mjs",
    nodeResolve: true,
    testFramework: {
        config: {
            ui: "bdd",
        }
    }
}