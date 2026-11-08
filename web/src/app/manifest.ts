import type { MetadataRoute } from "next";

// Makes the site installable as a PWA ("Add to Home Screen"), so the camera scan feels native.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Recall Radar",
    short_name: "Recall Radar",
    description: "Find out if anything you own has been recalled.",
    start_url: "/",
    display: "standalone",
    background_color: "#fafaf9",
    theme_color: "#b91c1c",
    icons: [{ src: "/favicon.ico", sizes: "any", type: "image/x-icon" }],
  };
}
