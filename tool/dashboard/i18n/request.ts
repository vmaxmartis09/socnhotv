import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";

const MODULES = ["video", "sources", "social", "nodes", "studio"] as const;

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;

  if (!locale || !routing.locales.includes(locale as any)) {
    locale = routing.defaultLocale;
  }

  const baseMessages = (await import(`../messages/${locale}.json`)).default;
  const mergedModules: Record<string, any> = {};

  for (const mod of MODULES) {
    try {
      const modMessages = (await import(`../messages/modules/${mod}.${locale}.json`)).default;
      Object.assign(mergedModules, modMessages);
    } catch {
      // module messages optional / not yet created
    }
  }

  return {
    locale,
    messages: {
      ...baseMessages,
      ...mergedModules,
    },
  };
});
