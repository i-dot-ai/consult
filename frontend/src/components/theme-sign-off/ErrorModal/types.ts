export  type SaveThemeError =
  | { type: "unexpected" | "theme-does-not-exist" }
  | {
      type: "edit-conflict" | "remove-conflict";
      lastModifiedBy: string;
      latestVersion: string;
    };