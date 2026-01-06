import ProfileButton from "./ProfileButton.svelte";

export default {
  name: "ProfileButton",
  component: ProfileButton,
  category: "Navigation",
  props: [{ name: "isSignedIn", value: false, type: "bool" }],
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
