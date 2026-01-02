import Header from "./Header.svelte";

const isSignedIn = $state(false);

export default {
  name: "Header",
  component: Header,
  props: [
    {
      name: "isSignedIn",
      value: isSignedIn,
      type: "bool",
    },
  ],
  stories: [
    {
      name: "Signed In",
      props: {
        isSignedIn: true,
      },
    },
    {
      name: "Not Signed In",
      props: {
        isSignedIn: false,
      },
    },
  ],
};
