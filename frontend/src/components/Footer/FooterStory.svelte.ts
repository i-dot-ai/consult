import Footer from "./Footer.svelte";

let isSignedIn = $state(false);

export default {
  name: "Footer",
  component: Footer,
  props: [],
  stories: [
    {
      name: "Default",
      props: {},
    },
  ],
};
