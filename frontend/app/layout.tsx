import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import Navbar from "@/components/Navbar";
import VoiceAssistant from "@/components/VoiceAssistant";
import ThemeBoot from "@/components/ThemeBoot";

export const metadata: Metadata = {
  title: "Maya — AI Shopping Mall",
  description: "An AI-first conversational shopping experience.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body className="min-h-screen">
          <ThemeBoot />
          <Navbar />
          <main className="pb-10">{children}</main>
          <VoiceAssistant />
        </body>
      </html>
    </ClerkProvider>
  );
}
