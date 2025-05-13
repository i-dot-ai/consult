import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";

export default {
    input: "consultation_analyser/lit/csr/index.mjs",
    output: {
        dir: "frontend/lit/",
        format: "es",
        sourcemap: true,
    },
    plugins: [
        resolve({
            browser: true,
            moduleDirectories: ["node_modules"],
        }),
        commonjs(),
    ]
};
