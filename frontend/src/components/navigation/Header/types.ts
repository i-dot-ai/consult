import { type Component, type Snippet } from "svelte";

export interface NavItem {
  label: string;
  url?: string;
  children?: NavItem[];
}

export interface Props {
  title: string;
  subtitle: string;
  pathParts: string[];
  navItems: NavItem[];
  icon: Component;
  endItems?: Snippet;
}