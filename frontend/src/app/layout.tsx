import type { Metadata, Viewport } from "next";
import { ToastProvider } from "@/components/Toast";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { I18nProvider } from "@/lib/i18n";
import "./globals.css";

export const metadata: Metadata = {
  title: "RescueForge — CAD zu Feuerwehr-Orientierungsplänen",
  description:
    "CAD-Gebäudepläne (DWG/DXF) automatisch in normkonforme Feuerwehr-Orientierungspläne umwandeln",
  icons: { icon: "/favicon.svg" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#111827",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de" className="dark">
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      </head>
      <body className="bg-gray-50 dark:bg-gray-950 min-h-screen transition-colors duration-300">
        <ErrorBoundary>
          <I18nProvider>
            <ToastProvider>{children}</ToastProvider>
          </I18nProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
