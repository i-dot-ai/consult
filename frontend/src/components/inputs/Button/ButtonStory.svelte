<script lang="ts">
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Search from "../../svg/material/Search.svelte";
  import Title from "../../Title.svelte";
  import Button from "./Button.svelte";

  let toggleButtonLightActive: boolean = true;
  let toggleButtonDarkActive: boolean = true;
  let toggleButtonPrimaryActive: boolean = true;
</script>

<div>
  <Title level={2} text="Default" />
  <Button>Click Here</Button>
</div>

<div>
  <Title level={2} text="Primary" />
  <Button variant="primary">Click Here</Button>
</div>

<div>
  <Title level={2} text="Ghost" />
  <Button variant="ghost">Click Here</Button>
</div>

<div>
  <Title level={2} text="Disabled" />
  <Button disabled={true}>Click Here</Button>
</div>

<div>
  <Title level={2} text="With Icon" />
  <Button>
    <MaterialIcon color="fill-neutral-400">
      <Search />
    </MaterialIcon>

    Click Here
  </Button>
</div>

<div>
  <Title level={2} text="With Toggle - Light" />
  <Button
    highlighted={toggleButtonLightActive}
    highlightVariant="light"
    handleClick={() => (toggleButtonLightActive = !toggleButtonLightActive)}
  >
    Click Here
  </Button>
</div>

<div>
  <Title level={2} text="With Toggle - Dark" />
  <Button
    highlighted={toggleButtonDarkActive}
    highlightVariant="dark"
    handleClick={() => (toggleButtonDarkActive = !toggleButtonDarkActive)}
  >
    Click Here
  </Button>
</div>

<div>
  <Title level={2} text="With Toggle - Primary" />
  <Button
    highlighted={toggleButtonPrimaryActive}
    highlightVariant="primary"
    handleClick={() => (toggleButtonPrimaryActive = !toggleButtonPrimaryActive)}
  >
    Click Here
  </Button>
</div>

<div>
  <Title level={2} text="With Click Handler" />
  <Button handleClick={() => alert("button clicked")}>Click Here</Button>
</div>

<div>
  <Title level={2} text="Size Xlarge" />
  <Button size="xl">Click Here</Button>
</div>

<div>
  <Title level={2} text="Size Large" />
  <Button size="lg">Click Here</Button>
</div>

<div>
  <Title level={2} text="Size Medium" />
  <Button size="md">Click Here</Button>
</div>

<div>
  <Title level={2} text="Size Small" />
  <Button size="sm">Click Here</Button>
</div>

<div>
  <Title level={2} text="Size XSmall" />
  <Button size="xs">Click Here</Button>
</div>

<div>
  <Title level={2} text="Full Width" />
  <Button fullWidth={true}>
    <span class="text-center w-full">Click Here</span>
  </Button>
</div>
