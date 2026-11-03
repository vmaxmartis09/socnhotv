import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import { Sidebar } from "@/components/navigation/Sidebar";
import { Header } from "@/components/navigation/Header";
import { BottomNav } from "@/components/navigation/BottomNav";
import { IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "@/app/globals.css";

const sans = IBM_Plex_Sans({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500"],
  variable: "--font-mono", /* taste-skill-ignore */
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Video Studio - SocNhoTV",
  description:
    "Nền tảng quản lý dự án video & sáng tạo hoạt hình 3D bằng AI Node Canvas",
};

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!routing.locales.includes(locale as any)) {
    notFound();
  }

  const messages = await getMessages();

  return (
    <html lang={locale} className={`${sans.variable} ${mono.variable}`} suppressHydrationWarning>
      <body className="h-dvh bg-background text-foreground font-sans antialiased flex overflow-hidden">
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0 h-dvh">
              <Header />
              {/* The sheet: white page inset 8px from the window's right and bottom edges */}
              <main className="flex flex-1 min-h-0 overflow-hidden bg-card pb-14 md:pb-0 md:mr-2 md:mb-2 md:rounded-2xl md:border md:border-border">
                {children}
              </main>
            </div>
            <BottomNav />
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
