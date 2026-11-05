import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import { Header } from "@/components/navigation/Header";
import { BottomNav } from "@/components/navigation/BottomNav";
import { AppRail } from "@/components/navigation/AppRail";
import { ConfirmHost } from "@/components/ui/ConfirmHost";
import { TooltipHost } from "@/components/ui/TooltipHost";
import { FloatingPanels } from "@/components/studio/FloatingPanels";
import { SocialHubHost } from "@/components/social/hub/SocialHubHost";
import { Suspense } from "react";
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
      <body className="h-dvh bg-background text-foreground font-sans antialiased flex overflow-clip">
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            <div className="relative flex h-dvh min-w-0 flex-1 flex-col">
              <Header />
              <main className="flex min-h-0 flex-1 overflow-clip bg-card pb-14 md:pb-0">
                {children}
              </main>
              <AppRail />
              <FloatingPanels />
            </div>
            <BottomNav />
            <ConfirmHost />
            <TooltipHost />
            <Suspense fallback={null}>
              <SocialHubHost />
            </Suspense>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
