import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Neighborhood Insights IL",
  description: "Discover and compare neighborhoods in Israel based on quality of life factors",
  manifest: "/manifest.json",
  icons: {
    icon: "/favicon.ico",
    apple: "/icon-192x192.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="he" dir="rtl">
      <body className={`${inter.className} bg-gray-50 text-gray-900`}>
        <div className="min-h-screen flex flex-col">
          <header className="bg-blue-600 text-white p-4 shadow-md">
            <h1 className="text-xl font-semibold">תובנות שכונות</h1>
          </header>
          <main className="flex-1 relative">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
