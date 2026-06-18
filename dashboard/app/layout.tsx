import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "projectsf — AI-Infrastructure & Real-Asset Research",
  description:
    "Equity valuation, supply-chain bottleneck mapping, and UK real-estate underwriting — one institutional research platform.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
