import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EstateFlow AI — Residential Lead Intelligence & Booking",
  description: "Production-grade AI Lead Management and Concurrency-Safe Site-Visit Booking Platform for Residential Real Estate in Ahmedabad",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#FBFBFA] text-[#0F172A] antialiased">
        {children}
      </body>
    </html>
  );
}
