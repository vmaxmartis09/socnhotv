import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import { Sidebar } from "@/components/navigation/Sidebar";
import { Header } from "@/components/navigation/Header";
import { BottomNav } from "@/components/navigation/BottomNav";
import "@/app/globals.css";

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
    <html lang={locale} suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased flex flex-col md:flex-row overflow-x-hidden">
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0 pb-16 md:pb-0">
              <Header />
              <main className="flex-1 overflow-y-auto">{children}</main>
            </div>
            <BottomNav />
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
