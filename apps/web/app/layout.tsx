import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shadowseed",
  description: "Product client for the canonical Shadowseed engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
