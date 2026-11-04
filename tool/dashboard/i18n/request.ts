import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;

  if (!locale || !routing.locales.includes(locale as any)) {
    locale = routing.defaultLocale;
  }

  const baseMessages = (await import(`../messages/${locale}.json`)).default;
  let videoMessages = {};
  let sourcesMessages = {};
  let socialMessages = {};

  try {
    videoMessages = (await import(`../messages/modules/video.${locale}.json`)).default;
  } catch {}
  try {
    sourcesMessages = (await import(`../messages/modules/sources.${locale}.json`)).default;
  } catch {}
  try {
    socialMessages = (await import(`../messages/modules/social.${locale}.json`)).default;
  } catch {}

  return {
    locale,
    messages: {
      ...baseMessages,
      ...videoMessages,
      ...sourcesMessages,
      ...socialMessages,
    },
  };
});
