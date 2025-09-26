import { vitePreprocess } from "@astrojs/svelte";
import { preprocessMeltUI, sequence } from "@melt-ui/pp";

export default {
  preprocess: sequence([vitePreprocess(), preprocessMeltUI()]),
};
