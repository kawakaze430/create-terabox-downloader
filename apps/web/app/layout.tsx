import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TeraBox File Inspector — Development Preview",
  description: "Independent software prototype for validating authorized TeraBox share links. File downloads are not connected yet.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
