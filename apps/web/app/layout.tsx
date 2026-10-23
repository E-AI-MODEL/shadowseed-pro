import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shadowseed",
  description: "Local client for the Shadowseed validation-gated memory engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
