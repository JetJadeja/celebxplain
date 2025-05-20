"use client";

import React from "react";
// import { ThemeProvider, StyleSheetManager } from "styled-components"; // No longer needed
// import original from "react95/dist/themes/original"; // No longer needed
import { JobProvider } from "@/lib/job-context";
// import isPropValid from "@emotion/is-prop-valid"; // No longer needed

// List of props used by react95 components that shouldn't reach the DOM (No longer needed)
// const react95Props = [
//   "active",
//   "fixed",
//   "fullWidth",
//   "shadow",
//   "square",
//   "primary",
//   // Add any other custom props from react95 components if needed
// ];

// This function determines if a prop should be forwarded to the DOM element (No longer needed)
// function shouldForwardProp(propName: string, target: any) {
//   if (typeof target === "string") {
//     // Don't forward non-standard HTML attributes or specific react95 props
//     return isPropValid(propName) && !react95Props.includes(propName);
//   }
//   // Forward all props to React components
//   return true;
// }

// This component wraps children with client-side providers
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    // <StyleSheetManager shouldForwardProp={shouldForwardProp}> // No longer needed
    //   <ThemeProvider theme={original}> // No longer needed
    //   </ThemeProvider>
    // </StyleSheetManager>
    <JobProvider>{children}</JobProvider>
  );
}
