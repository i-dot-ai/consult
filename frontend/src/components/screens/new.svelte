<script lang="ts">
  export const createDebouncedValue = <T,>(
    getValue: () => T,
    delay: number = 500,
  ) => {
    let debouncedValue = $state(getValue()) as T;

    $effect(() => {
      const currentValue = getValue();
      const timeoutId = setTimeout(() => {
        debouncedValue = currentValue;
      }, delay);

      return () => clearTimeout(timeoutId);
    });

    return {
      get value() {
        return debouncedValue;
      },
    };
  };
</script>
