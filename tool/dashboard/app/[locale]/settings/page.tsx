"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useStudioStore } from "@/store";
import { useTheme } from "@/components/theme/ThemeProvider";
import { usePathname, useRouter } from "@/i18n/routing";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Sun, Moon, Laptop, Globe, Database, ShieldCheck, DollarSign } from "lucide-react";

export default function SettingsPage() {
  const t = useTranslations("settings");
  const { theme, setTheme } = useTheme();
  const { isMockMode, setIsMockMode, spendingLimitUsd, setSpendingLimitUsd } =
    useStudioStore();
  const pathname = usePathname();
  const router = useRouter();

  const changeLocale = (newLocale: "vi" | "en") => {
    router.replace(pathname, { locale: newLocale });
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-foreground">
          {t("title")}
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          Tùy chỉnh giao diện, ngôn ngữ, bộ lưu trữ và giới hạn ngân sách
        </p>
      </div>

      {/* Theme Setting */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sun className="w-4 h-4 text-primary" />
            {t("themeMode")}
          </CardTitle>
          <CardDescription>
            Giao diện dịu nhẹ, không đen tuyệt đối hoặc trắng tinh, bảo vệ thị lực
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: "light", label: "Sáng", icon: Sun },
              { id: "dark", label: "Tối", icon: Moon },
              { id: "system", label: "Hệ thống", icon: Laptop },
            ].map((item) => {
              const Icon = item.icon;
              const isSelected = theme === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setTheme(item.id as any)}
                  className={`flex flex-col items-center justify-center p-3.5 rounded-lg border text-xs font-semibold transition-all ${
                    isSelected
                      ? "border-primary bg-primary/10 text-primary shadow-subtle"
                      : "border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted/40"
                  }`}
                >
                  <Icon className="w-4 h-4 mb-1.5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Language Setting */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Globe className="w-4 h-4 text-primary" />
            {t("language")}
          </CardTitle>
          <CardDescription>
            Chuyển đổi tức thì không cần tải lại toàn bộ trang
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 max-w-sm">
            <Button
              variant="outline"
              size="md"
              onClick={() => changeLocale("vi")}
              className="justify-start font-medium"
            >
              🇻🇳 Tiếng Việt
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={() => changeLocale("en")}
              className="justify-start font-medium"
            >
              🇺🇸 English
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Storage Repository Setting */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Database className="w-4 h-4 text-primary" />
            {t("storageBackend")}
          </CardTitle>
          <CardDescription>
            Kiến trúc trừu tượng Repository phân tách hoàn toàn giữa giao diện và nguồn dữ liệu
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="p-3.5 rounded-lg border border-primary/40 bg-primary/5 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-semantic-success shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <span className="font-semibold text-foreground block">
                LocalRepository (IndexedDB) — Đang kích hoạt
              </span>
              <p className="text-muted-foreground leading-relaxed">
                Toàn bộ dữ liệu dự án, nhân vật và kịch bản được lưu trữ cục bộ trên máy duyệt của bạn. Không cần tạo tài khoản hay kết nối mạng.
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded-lg border border-border bg-muted/20 opacity-70 flex items-start gap-3">
            <Database className="w-5 h-5 text-muted-foreground shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <span className="font-semibold text-foreground block">
                Supabase Cloud Repository (Tùy chọn)
              </span>
              <p className="text-muted-foreground leading-relaxed">
                Tự động kích hoạt khi có biến môi trường NEXT_PUBLIC_SUPABASE_URL. Cho phép đồng bộ đa thiết bị và xác thực OAuth.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Budget & Mock Safety Guard */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-primary" />
            Bảo vệ chi phí API & Mock Mode
          </CardTitle>
          <CardDescription>
            Chế độ chạy thử giả lập ảnh/video miễn phí giúp kiểm thử giao diện mà không tốn tiền API
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border">
            <div>
              <span className="font-semibold text-foreground block">
                Chế độ Chạy thử (Mock Mode)
              </span>
              <span className="text-muted-foreground text-[11px]">
                Tạo hình ảnh và video mẫu giả lập ngay trên trình duyệt
              </span>
            </div>
            <button
              onClick={() => setIsMockMode(!isMockMode)}
              className={`px-3 py-1.5 rounded-md font-semibold text-xs transition-colors ${
                isMockMode
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {isMockMode ? "ĐANG BẬT" : "ĐANG TẮT"}
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border">
            <div>
              <span className="font-semibold text-foreground block">
                Ngưỡng cảnh báo chi phí
              </span>
              <span className="text-muted-foreground text-[11px]">
                Hộp xác nhận Tool Approval sẽ bật lên khi chi phí vượt ngưỡng này
              </span>
            </div>
            <span className="font-mono font-bold text-foreground text-sm">
              ${spendingLimitUsd.toFixed(2)} USD
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
