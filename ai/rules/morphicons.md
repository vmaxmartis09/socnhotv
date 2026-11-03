# QUY CHUẨN HỆ THỐNG ICON MORPHICONS (MẶC ĐỊNH BẮT BUỘC)

> [!CRITICAL]
> **THƯ VIỆN ICON DUY NHẤT ĐƯỢC PHÉP SỬ DỤNG TRONG TOÀN BỘ DỰ ÁN LÀ MORPHICONS (https://www.morphicons.com/)**
> Tuyệt đối không import hoặc cài đặt lại `lucide-react`. Mọi icon trong dự án phải đi qua `MorphIcon` hoặc registry `@/components/ui/icons`.

---

## 1. Nguyên tắc hoạt động
- **Công nghệ cốt lõi:** `morphicons` (npm: `morphicons/react`), tính toán giải thuật Procrustes 2D similarity để morphing mượt mà giữa bất kỳ 2 icon nào với spring physics.
- **Nguồn dữ liệu hình học icon:** Package `lucide` (cung cấp data structures `IconNode`, không chứa React component wrappers cồng kềnh).

## 2. Chuẩn import & Sử dụng
- **Cách 1 (Pre-configured Icon Component):**
  ```tsx
  import { Sun, Moon, Film, Plus, Sparkles } from "@/components/ui/icons";

  <Plus className="w-4 h-4 mr-1.5" />
  <Film className="w-4 h-4 shrink-0" strokeWidth={1.5} />
  ```

- **Cách 2 (Morphing theo trạng thái - Khuyến nghị cho interactive elements):**
  ```tsx
  import { MorphIcon, SunNode, MoonNode, LaptopNode } from "@/components/ui/icons";

  const themeIcon = theme === "system" ? LaptopNode : resolvedTheme === "dark" ? MoonNode : SunNode;

  <button onClick={toggleTheme}>
    <MorphIcon icon={themeIcon} className="h-4 w-4" strokeWidth={1.5} spring="snappy" />
  </button>
  ```

## 3. Cấm tuyệt đối
- Không dùng `lucide-react`.
- Không tạo SVG inline lặp lại hoặc import thư viện icon khác (như `react-icons`, `@heroicons/react`).
