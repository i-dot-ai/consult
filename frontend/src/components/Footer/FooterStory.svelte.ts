import Footer from "./Footer.svelte";

const isSignedIn = $state(false);

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
